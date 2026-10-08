from sqlalchemy import delete, insert, select
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session_maker
from app.logger import logger


class BaseDAO:
    model = None

    @classmethod
    async def get_all(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_by_id(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filter_by)
            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_one_or_none(cls, **filter_by):
        async with async_session_maker() as session:
            query = select(cls.model.__table__.columns).filter_by(**filter_by)
            result = await session.execute(query)
            return result.mappings().one_or_none()

    @classmethod
    async def add(cls, **data):
        query = insert(cls.model).values(**data).returning(cls.model.id)
        try:
            async with async_session_maker() as session:
                result = await session.execute(query)
                await session.commit()
                return result.mappings().first()
        except SQLAlchemyError:
            logger.error(
                "Cannot insert data into table",
                extra={"table": cls.model.__tablename__},
                exc_info=True,
            )
            return None

    @classmethod
    async def delete(cls, **filter_by):
        async with async_session_maker() as session:
            query = delete(cls.model).filter_by(**filter_by)
            await session.execute(query)
            await session.commit()
