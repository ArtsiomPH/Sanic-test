from sanic import Sanic

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from auth import auth, get_current_active_user
from users import users
from goods import goods
from payment import payment

from contextvars import ContextVar

SQLALCHEMY_DB_URL = "postgresql+asyncpg://test_acc:12345@localhost/sanic_test"

app = Sanic('test_app')
app.blueprint(auth)
app.blueprint(users)
app.blueprint(goods)
app.blueprint(payment)

engine = create_async_engine(SQLALCHEMY_DB_URL, echo=True)
_sessionmaker = sessionmaker(engine, AsyncSession, expire_on_commit=False)
_base_model_session_ctx = ContextVar("session")


@app.middleware("request")
async def inject_session(request):
    request.ctx.session = _sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)


@app.middleware("request")
async def add_current_user(request):
    if request.token:
        request.ctx.current_user = await get_current_active_user(request, request.token)


@app.middleware("response")
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()
