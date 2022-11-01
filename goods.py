from sanic import Blueprint, Request, json, text

from models import Goods
from decorators import admin_only, active_user_only

from sqlalchemy import select, update, delete

goods = Blueprint('goods', url_prefix='/goods')


@goods.get('/')
@active_user_only
async def get_goods_list(request: Request):
    session = request.ctx.session

    async with session.begin():
        result = await session.execute(select(Goods).order_by(Goods.id))
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

    return json([item.to_dict() for item in goods_to_add], status=201)


@goods.route('/<pk:int>', methods=['GET', 'PATCH', 'DELETE'])
@admin_only
async def update_delete_goods(request: Request, pk: int):
    session = request.ctx.session
    if request.method == 'GET':
        async with session.begin():
            result = await session.execute(select(Goods).where(Goods.id == pk))

        item = result.scalar()
        if item is None:
            return text(f'Goods with id = {pk} is not exist.', status=400)

        return json(item.to_dict())

    if request.method == 'PATCH':
        body: dict = request.json

        async with session.begin():
            result_rows = await session.execute(update(Goods).where(Goods.id == pk).values(**body).returning(
                Goods.id,
                Goods.title,
                Goods.description,
                Goods.price
            ))

        goods_rows: tuple = result_rows.first()
        if goods_rows is None:
            return text(f'Goods with id = {pk} is not exist.', status=400)

        pk, title, description, price = goods_rows
        return json(Goods(id=pk, title=title, description=description, price=price).to_dict())

    if request.method == 'DELETE':
        async with session.begin():
            result = await session.execute(delete(Goods).where(Goods.id == pk).returning(Goods.title))

        title = result.first()
        if title is None:
            return text(f'Goods with id = {pk} is not exist.', status=400)

        return text(f'{title[0]} was deleted')



