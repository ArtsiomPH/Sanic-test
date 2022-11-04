from sanic import Blueprint, Request, text

from goods import get_element_by_id
from models import Goods, Bill
from decorators import active_user_only

from sqlalchemy import update

payment = Blueprint('payment', url_prefix='/payment')


async def update_user_balance(request, bill_id, balance):
    session = request.ctx.session

    async with session.begin():
        await session.execute(update(Bill).where(Bill.id == bill_id).values(balance=balance))


@payment.post('/goods/<goods_id:int>')
@active_user_only
async def buy_goods(request: Request, goods_id: int):
    bill_id = int(request.form.get('bill_id'))

    if bill_id is None:
        return text('Please enter your bill\'s id', status=400)

    current_user = request.ctx.current_user
    bills_list = [bill['bill_id'] for bill in current_user.to_dict().get('bills')]

    if bill_id not in bills_list:
        return text('Please enter your own bill\'s id')

    session = request.ctx.session

    goods = await get_element_by_id(session, Goods, goods_id)

    bill_balance = [bill_object.balance for bill_object in current_user.bill if bill_object.id == bill_id][0]

    if goods.price > bill_balance:
        return text('Operation prohibited. Not enough funds')

    new_balance = bill_balance - goods.price

    request.app.add_task(update_user_balance(request, bill_id, new_balance))

    return text('Product purchased')
