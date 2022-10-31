from sanic import Sanic

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from views import signin

from contextvars import ContextVar

from models import User

SQLALCHEMY_DB_URL = "postgresql+asyncpg://test_acc:12345@localhost/sanic_test"

app = Sanic('test_app')
app.blueprint(signin)

engine = create_async_engine(SQLALCHEMY_DB_URL, echo=True)
_sessionmaker = sessionmaker(engine, AsyncSession, expire_on_commit=False)
_base_model_session_ctx = ContextVar("session")


@app.middleware("request")
async def inject_session(request):
    request.ctx.session = _sessionmaker()
    request.ctx.session_ctx_token = _base_model_session_ctx.set(request.ctx.session)


@app.middleware("response")
async def close_session(request, response):
    if hasattr(request.ctx, "session_ctx_token"):
        _base_model_session_ctx.reset(request.ctx.session_ctx_token)
        await request.ctx.session.close()





