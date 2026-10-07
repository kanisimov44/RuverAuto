from typing import Annotated

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.pool import NullPool

from app.config import settings

# В тестах каждый тест работает в своём event loop, поэтому соединения
# не переиспользуются между ними.
engine_params = {"poolclass": NullPool} if settings.MODE == "TEST" else {}

engine = create_async_engine(settings.DATABASE_URL, **engine_params)

async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

intpk = Annotated[int, mapped_column(primary_key=True)]


class Base(DeclarativeBase):
    pass
