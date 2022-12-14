from dataclasses import dataclass
from datetime import datetime, timedelta

from jose import jwt, JWTError

from sanic import Request, json, Blueprint, text
from sanic_ext import validate
from sanic.exceptions import SanicException, Unauthorized
from models import User

from passlib.context import CryptContext

from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update

auth = Blueprint("auth", url_prefix="/auth")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "b5640c66f204d7e8f02828912beea154840e03e6d7cd252abda52d9a2c1a7bff"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30
TEMP_ACCESS_TOKEN_EXPIRE_DAYS = 1


@dataclass
class AuthForm:
    login: str
    password: str


def create_access_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


async def authenticate_user(request: Request, login: str, password: str) -> User | bool:
    user = await get_user(request, login)

    if not user:
        return False
    if not verify_password(password, user.password):
        return False

    return user


async def get_all_user_objects(session):
    result = await session.execute(select(User))
    users = result.all()
    return users


async def get_current_user(request: Request, token: str):
    credentials_exception = SanicException(
        status_code=401,
        message="Could not validate credentials",
    )
    expiration_error = SanicException(message="Token expired")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = payload.get("login")
        expire = payload.get("exp")
        if login is None:
            raise credentials_exception
        if datetime.fromtimestamp(expire) < datetime.utcnow():
            raise expiration_error

    except JWTError:
        raise credentials_exception
    user = await get_user(request, login)
    if user is None:
        raise credentials_exception
    return user


async def get_user(request: Request, login: str):
    session = request.ctx.session
    async with session.begin():
        result = await session.execute(
            select(User).where(User.login == login).options(selectinload(User.bill))
        )
    user = result.scalar()
    return user


async def get_current_active_user(request: Request, token: str):
    user = await get_current_user(request, token)
    if not user.is_active:
        raise SanicException(status_code=400, message="Inactive user")
    return user


def get_hashed_password(password: str):
    return pwd_context.hash(password)


@auth.post("/")
@validate(form=AuthForm)
async def create_user(request: Request, body: AuthForm):
    session = request.ctx.session

    login = body.login
    hashed_password = get_hashed_password(body.password)

    try:
        async with session.begin():
            users = await get_all_user_objects(session)
            if not users:
                user = User(
                    login=login, password=hashed_password, is_admin=True, is_active=True
                )
                session.add(user)
                return text(f"Hello admin {user.login}!", status=201)
            else:
                user = User(login=login, password=hashed_password)
                session.add(user)
    except IntegrityError:
        return json(
            "User with login '{}' is exist. "
            "Please choose a different username.".format(login),
            status=400,
        )

    temp_token_expire = timedelta(days=TEMP_ACCESS_TOKEN_EXPIRE_DAYS)
    temp_token = create_access_token({"login": user.login}, temp_token_expire)
    return text(
        f"Follow this link for activation. "
        f"http://127.0.0.1:8000/auth/activation/"
        f"?temp_token={temp_token}"
    )


@auth.get("/activation/")
async def user_activation(request: Request):
    temp_token = request.args.get("temp_token")
    session = request.ctx.session
    user = await get_current_user(request, temp_token)
    if not user.is_active:
        async with session.begin():
            await session.execute(
                update(User).where(User.login == user.login).values(is_active=True)
            )
        return text(
            "Your account was activated, "
            "please follow the link to get a permanent token."
            "http://127.0.0.1:8000/auth/token"
        )
    return text("Your account is already activated")


@auth.post("/token")
@validate(form=AuthForm)
async def get_access_token(request: Request, body: AuthForm):
    login = body.login
    password = body.password
    user = await authenticate_user(request, login, password)
    if not user.is_active:
        return text(status=401, body="Inactive user")

    if not user:
        raise Unauthorized(status_code=401, message="Incorrect username or password")

    access_token_expires = timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"login": user.login}, expires_delta=access_token_expires
    )
    return json({"access_token": access_token, "token_type": "bearer"})
