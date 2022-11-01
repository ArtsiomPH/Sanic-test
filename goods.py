from sanic import Blueprint, Request, json

from models import Goods
from decorators import admin_only, active_user_only

from sqlalchemy import select

goods = Blueprint('goods', url_prefix='/goods')


@goods.get('/')
@active_user_only
async def get_goods_list(request: Request):
    session = request.ctx.session

    async with session.begin():
        result = await session.execute(select(Goods))
        goods_list = result.all()

    return json([item[0].to_dict for item in goods_list])
