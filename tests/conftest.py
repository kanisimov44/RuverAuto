import os

# Настройки читаются при импорте app, поэтому окружение задаётся до него.
# Тесты всегда работают с отдельной базой и никогда с рабочей.
os.environ["MODE"] = "TEST"
os.environ["POSTGRES_DB"] = os.environ.get("TEST_POSTGRES_DB", "ruverauto_test")

from datetime import date  # noqa: E402

import anyio  # noqa: E402
import asyncpg  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import async_session_maker  # noqa: E402
from app.main import app as fastapi_app  # noqa: E402
from app.main_content.models import AboutUsImages, MainContent  # noqa: E402
from app.news.models import News, NewsImages  # noqa: E402
from app.products.models import Products, ProductsImages, ProductsInfo  # noqa: E402
from app.text_pages.models import TextPages  # noqa: E402
from app.users.auth import get_password_hash  # noqa: E402
from app.users.models import Roles, Users  # noqa: E402

assert settings.MODE == "TEST"

PASSWORD = "secret-password"


async def _recreate_database() -> None:
    connection = await asyncpg.connect(
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT,
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database="postgres",
    )
    try:
        await connection.execute(f'DROP DATABASE IF EXISTS "{settings.POSTGRES_DB}" WITH (FORCE)')
        await connection.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
    finally:
        await connection.close()


async def _fill_database() -> None:
    async with async_session_maker() as session:
        content = MainContent(
            logo="logo.png",
            phone="8 800 000-00-00",
            email="test@example.com",
            header_title="Рувер-Авто",
            about_us_title="О компании",
        )
        content.images.append(AboutUsImages(image_name="about.webp"))
        session.add(content)

        session.add(
            TextPages(
                our_contacts="Контакты для теста",
                delivery_and_payment="Доставка для теста",
                privacy_policy="Политика для теста",
                user_agreement="Соглашение для теста",
            )
        )

        truck = Products(
            name="Самосвал",
            description="Описание самосвала " * 10,
            price=5_000_000,
            label=True,
            is_active=True,
        )
        truck.images.extend(
            [ProductsImages(image_name="truck_1.webp"), ProductsImages(image_name="truck_2.webp")]
        )
        truck.characteristics.append(
            ProductsInfo(name_of_characteristic="Оси", value_of_characteristic="3")
        )
        session.add_all(
            [
                truck,
                Products(name="Фургон", price=None, label=None, is_active=True),
                Products(name="Скрытый товар", is_active=False),
            ]
        )

        old_news = News(title="Старая новость", date_of_the_news=date(2024, 1, 10), is_active=True)
        old_news.images.append(NewsImages(news_image_name="news_old.webp"))
        session.add_all(
            [
                old_news,
                News(title="Свежая новость", date_of_the_news=date(2024, 5, 20), is_active=True),
                News(title="Черновик", date_of_the_news=date(2024, 6, 1), is_active=False),
            ]
        )

        hashed = get_password_hash(PASSWORD)
        session.add_all(
            [
                Users(username="admin", hashed_password=hashed, role=Roles.ADMIN),
                Users(username="user", hashed_password=hashed, role=Roles.USER),
                Users(
                    username="blocked", hashed_password=hashed, role=Roles.ADMIN, is_active=False
                ),
            ]
        )
        await session.commit()


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    """Чистая база, схема из миграций alembic и тестовые данные."""
    await _recreate_database()
    # env.py миграций синхронный, поэтому запускаем его в отдельном потоке
    await anyio.to_thread.run_sync(command.upgrade, Config("alembic.ini"), "head")
    await _fill_database()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
async def ids() -> dict[str, int]:
    """Идентификаторы тестовых записей по названиям."""
    async with async_session_maker() as session:
        products = (await session.execute(select(Products.name, Products.id))).all()
        news = (await session.execute(select(News.title, News.id))).all()
    return {name: id_ for name, id_ in [*products, *news]}
