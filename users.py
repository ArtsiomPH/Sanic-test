from auth import get_all_user_objects
from models import User

from sanic import Blueprint, json, Request

from sqlalchemy import select, update

from decorators import admin_only

users = Blueprint('users', url_prefix='/users')


@users.get('/')
@admin_only
async def get_users_list(request):
    session = request.ctx.session
    async with session.begin():
        users_list = await get_all_user_objects(session)
    return json([user[0].to_dict() for user in users_list])


@users.patch('/<pk:int>')
@admin_only
async def change_user_status(request: Request, pk: int):
    status: str = request.json.get('is_active')

    session = request.ctx.session
    async with session.begin():
        await session.execute(update(User).where(User.id == pk).values(is_active=(status.lower() == 'true')))
        res = await session.execute(select(User).where(User.id == pk))
        changed_user = res.scalar()

    return json({'changed': changed_user.to_dict()})
