from models import User

from sanic import Blueprint, json, Request, text

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from decorators import admin_only, active_user_only

users = Blueprint('users', url_prefix='/users')


@users.get('/')
@admin_only
async def get_users_list(request: Request):
    session = request.ctx.session
    async with session.begin():
        res_rows = await session.execute(select(User).options(selectinload(User.bill)))

    user_objects = res_rows.scalars()

    return json([user.to_dict() for user in user_objects])


@users.patch('/<pk:int>')
@admin_only
async def change_user_status(request: Request, pk: int):
    status: str = request.json.get('is_active')
    if status is None:
        return text("Please enter the required status.", status=400)

    session = request.ctx.session
    async with session.begin():
        result_rows = await session.execute(update(User).where(User.id == pk)
                                            .values(is_active=(status.lower() == 'true'))
                                            .returning(User.id,
                                                       User.login,
                                                       User.is_admin,
                                                       User.is_active))
    user_rows: tuple = result_rows.first()

    if user_rows is None:
        return text(f'User with id = {pk} is not exist.', status=400)

    pk, login, is_admin, is_active = user_rows
    return json({'changed': User(id=pk, login=login, is_admin=is_admin, is_active=is_active).to_dict()})


@users.get('/me')
@active_user_only
async def current_user_info(request):
    current_user = request.ctx.current_user

    return json(current_user.to_dict())




