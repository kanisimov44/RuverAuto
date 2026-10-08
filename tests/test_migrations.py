from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext

from app.database import Base, engine


async def test_models_match_migrations():
    """Схема после всех миграций совпадает с моделями: никто не забыл миграцию."""

    def compare(connection):
        context = MigrationContext.configure(connection)
        return compare_metadata(context, Base.metadata)

    async with engine.connect() as connection:
        diff = await connection.run_sync(compare)

    assert diff == []
