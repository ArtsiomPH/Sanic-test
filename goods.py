from sanic import Blueprint, Request, json, text

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

    return json([item[0].to_dict() for item in goods_list])


@goods.post('/')
@admin_only
async def create_goods(request: Request):
    body = request.json

    goods_to_add = [Goods(**body)] if type(body) == dict else [Goods(**item) for item in body]

    session = request.ctx.session
    async with session.begin():
        session.add_all(goods_to_add)

    return json([item.to_dict() for item in goods_to_add])

