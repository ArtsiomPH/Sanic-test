from models import User, Transaction

from sanic import Blueprint, json, Request, text

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from decorators import admin_only, active_user_only

users = Blueprint("users", url_prefix="/users")


@users.get("/")
@admin_only
async def get_users_list(request: Request):
    session = request.ctx.session
    async with session.begin():
        res_rows = await session.execute(select(User).options(selectinload(User.bill)))

    user_objects = res_rows.scalars()

    return json([user.to_dict() for user in user_objects])


@users.patch("/<user_id:int>")
@admin_only
async def change_user_status(request: Request, user_id: int):
    status: str = request.json.get("is_active")
    if status is None:
        return text("Please enter the required status.", status=400)

    session = request.ctx.session
    async with session.begin():
        result_rows = await session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=(status.lower() == "true"))
            .returning(User.id, User.login, User.is_admin, User.is_active)
        )
    user_rows: tuple = result_rows.first()

    if user_rows is None:
        return text(f"User with id = {user_id} is not exist.", status=400)

    pk, login, is_admin, is_active = user_rows
    return json(
        {
            "changed": User(
                id=pk, login=login, is_admin=is_admin, is_active=is_active
            ).to_dict()
        }
    )


@users.get("/me")
@active_user_only
async def get_current_user_info(request: Request):
    current_user: User = request.ctx.current_user
    return json(current_user.to_dict())


@users.get("/me/transactions")
@active_user_only
async def get_current_user_transaction_history(request: Request):
    current_user: User = request.ctx.current_user
    session = request.ctx.session

    bills = (
        [bill["bill_id"] for bill in current_user.to_dict().get("bills")]
        if current_user.to_dict().get("bills")
        else []
    )

    async with session.begin():
        result_rows = await session.execute(
            select(Transaction).where(Transaction.bill_id.in_(bills))
        )

    transactions = result_rows.scalars()
    return json([transaction.to_dict() for transaction in transactions])
