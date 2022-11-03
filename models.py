from sqlalchemy import Column, ForeignKey, String, BOOLEAN, Integer, Text, Numeric, DATETIME
from sqlalchemy.orm import declarative_base, relationship

from datetime import datetime

Base = declarative_base()


class BaseModel(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True, index=True)


class User(BaseModel):
    __tablename__ = "Users"

    login = Column(String, unique=True)
    password = Column(String())
    is_admin = Column(BOOLEAN, default=False)
    is_active = Column(BOOLEAN, default=False)
    bill = relationship("Bill")

    def to_dict(self) -> dict:
        if self.bill:
            return {'id': self.id, 'login': self.login, 'is_active': self.is_active,
                    'bills': [bl.to_dict() for bl in self.bill]}
        return {'id': self.id, 'login': self.login, 'is_active': self.is_active, 'is_admin': self.is_admin}


class Goods(BaseModel):
    __tablename__ = "Goods"

    title = Column(String(length=100))
    description = Column(Text)
    price = Column(Numeric(precision=8, scale=2))

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description, 'price': self.price}


class Bill(BaseModel):
    __tablename__ = "Bill"

    user_id = Column(Integer, ForeignKey('Users.id'))
    balance = Column(Numeric(precision=8, scale=2))
    transaction = relationship('Transaction')

    def to_dict(self):
        return {'bill_id': self.id, 'balance': self.balance}


class Transaction(BaseModel):
    __tablename__ = "Transaction"

    date = Column(DATETIME, default=datetime.utcnow())
    bill_id = Column(Integer, ForeignKey('Bill.id'))
    amount = Column(Numeric(precision=8, scale=2))

    def to_dict(self):
        return {'transaction_id': self.id, 'date': str(self.date), 'bill_id': self.bill_id, 'amount': self.amount}




