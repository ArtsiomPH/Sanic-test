from dataclasses import dataclass

from sanic import Blueprint, Request, text
from sanic_ext import validate
from sanic.exceptions import SanicException

from goods import get_element_by_id
from models import Goods, Bill, Transaction, User
from decorators import active_user_only

from sqlalchemy import update

from Crypto.Hash import SHA1

payment = Blueprint('payment', url_prefix='/payment')

PRIVATE_KEY = 'c26b2616287edb0c34537661f452ed8175891214f15d8c97ca01dc2606a08ad7'


@dataclass
class WebhookBody:
    signature: str
    transaction_id: int
    user_id: int
    bill_id: int
    amount: float


async def add_new_transaction(request: Request, body: WebhookBody):
    session = request.ctx.session
    async with session.begin():
        new_transaction = Transaction(id=body.transaction_id, bill_id=body.bill_id, amount=body.amount)
        session.add(new_transaction)
        await session.execute(update(Bill).where(Bill.id == body.bill_id).values(balance=Bill.balance + body.amount))


def check_signature(body: WebhookBody):
    new_signature = SHA1.new()
    new_signature.update(f'{PRIVATE_KEY}:{body.transaction_id}:{body.user_id}:{body.bill_id}:{body.amount}'.encode())

    if body.signature == new_signature.hexdigest():
        return True

    return False


async def update_user_balance(request: Request, bill_id: int, price: float):
    session = request.ctx.session

    async with session.begin():
        await session.execute(update(Bill).where(Bill.id == bill_id).values(balance=Bill.balance - price))


@payment.post('/goods/<goods_id:int>')
@active_user_only
async def buy_goods(request: Request, goods_id: int):
    bill_id = request.form.get('bill_id')
    if bill_id is None:
        return text('Please enter your bill\'s id', status=400)

    bill_id = int(bill_id)
    current_user: User = request.ctx.current_user
    bills_list = [bill['bill_id'] for bill in current_user.to_dict().get('bills')]
    if bill_id not in bills_list:
        return text('Please enter your own bill\'s id')

    session = request.ctx.session
    goods = await get_element_by_id(session, Goods, goods_id)

    bill_balance: float = [bill_object.balance for bill_object in current_user.bill if bill_object.id == bill_id][0]

    if goods.price > bill_balance:
        return text('Operation prohibited. Not enough funds')

    request.app.add_task(update_user_balance(request, bill_id, goods.price))

    return text('Product purchased', status=202)


@payment.post('/webhook')
@validate(json=WebhookBody)
async def refill(request: Request, body: WebhookBody):
    signature_verified: bool = check_signature(body)

    if not signature_verified:
        raise SanicException(message='Signature verification error', status_code=403)

    request.app.add_task(add_new_transaction(request, body))
    return text('Transaction has been processed', status=202)
