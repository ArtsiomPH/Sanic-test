from sanic import Blueprint

from signin import *

from decorators import admin_only

users = Blueprint('users', url_prefix='/users')


@users.get('/')
@admin_only
async def get_users_list(request):
    session = request.ctx.session
    async with session.begin():
        users_list = await get_all_user_objects(session)
    return json([user[0].to_dict() for user in users_list])


