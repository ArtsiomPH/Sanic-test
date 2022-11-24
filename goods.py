from sanic import Blueprint, Request, json, text
from sanic.exceptions import NotFound

from models import Goods, Bill
from decorators import admin_only, active_user_only

from sqlalchemy import select, update, delete

goods = Blueprint("goods", url_prefix="/goods")


async def get_element_by_id(session, model: Goods, element_id: int):
    async with session.begin():
        result = await session.execute(select(model).where(model.id == element_id))

        item = result.scalar()
        if item is None:
            raise NotFound(
                message=f"{model.__name__} with id = {element_id} is not exist."
            )
    return item


@goods.get("/")
@active_user_only
async def get_goods_list(request: Request):
    session = request.ctx.session

    async with session.begin():
        result = await session.execute(select(Goods).order_by(Goods.id))
        goods_list = result.scalars()

    return json(
        [
            item.to_dict()
            | {"buy_now": f"http://127.0.0.1:8000/payment/goods/{item.id}"}
            for item in goods_list
        ]
    )


@goods.post("/")
@admin_only
async def create_goods(request: Request):
    body = request.json

    goods_to_add = (
        [Goods(**body)] if type(body) == dict else [Goods(**item) for item in body]
    )

    session = request.ctx.session
    async with session.begin():
        session.add_all(goods_to_add)

    return json([item.to_dict() for item in goods_to_add], status=201)


@goods.route("/<goods_id:int>", methods=["GET", "PATCH", "DELETE"])
@admin_only
async def get_update_delete_goods(request: Request, goods_id: int):
    session = request.ctx.session
    if request.method == "GET":
        goods = await get_element_by_id(session, Goods, goods_id)

        return json(goods.to_dict())

    if request.method == "PATCH":
        body: dict = request.json

        async with session.begin():
            result_rows = await session.execute(
                update(Goods)
                .where(Goods.id == goods_id)
                .values(**body)
                .returning(Goods.id, Goods.title, Goods.description, Goods.price)
            )

        goods_rows = result_rows.scalar()
        if goods_rows is None:
            raise NotFound(f"Goods with id = {goods_id} is not exist.")

        pk, title, description, price = goods_rows
        return json(
            Goods(id=pk, title=title, description=description, price=price).to_dict()
        )

    if request.method == "DELETE":
        async with session.begin():
            result = await session.execute(
                delete(Goods).where(Goods.id == goods_id).returning(Goods.title)
            )

        title = result.scalar()
        if title is None:
            raise NotFound(f"Goods with id = {goods_id} is not exist.")

        return text(f"{title} was deleted")
