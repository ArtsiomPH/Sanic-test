from sqlalchemy import Column, ForeignKey, String, BOOLEAN, Integer, Text, Numeric
from sqlalchemy.orm import declarative_base, relationship

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

    def to_dict(self):
        return {'id': self.id, 'login': self.login, 'is_active': self.is_active, 'is_admin': self.is_admin}


class Goods(BaseModel):
    __table_name__ = "Goods"

    title = Column(String, length=100)
    description = Column(Text)
    price = Column(Numeric, precision=8, scale=2)

    def to_dict(self):
        return {'id': self.id, 'title': self.title, 'description': self.description, 'price': self.price}

