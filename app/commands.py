"""Служебные команды.

python -m app.commands create-admin <логин> [--password <пароль>]
python -m app.commands seed
"""

import argparse
import asyncio
import getpass
import io
from datetime import date, timedelta

from PIL import Image, ImageDraw
from sqlalchemy import func, select
from starlette.datastructures import UploadFile

from app.config import settings
from app.database import async_session_maker, engine
from app.main_content.models import AboutUsImages, MainContent
from app.news.models import News, NewsImages
from app.products.models import Products, ProductsImages, ProductsInfo
from app.text_pages.models import TextPages
from app.users.auth import get_password_hash
from app.users.models import Roles, Users


async def create_admin(username: str, password: str) -> None:
    async with async_session_maker() as session:
        exists = await session.scalar(select(Users.id).filter_by(username=username))
        if exists:
            raise SystemExit(f"Пользователь {username!r} уже существует")

        session.add(
            Users(
                username=username,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
                role=Roles.ROOT,
            )
        )
        await session.commit()
    print(f"Администратор {username!r} создан")


# --- Демо-данные ----------------------------------------------------------

PALETTE = ["#1f3b57", "#2f5d50", "#6b3e26", "#4a4e69", "#7a1f2b", "#2d4059"]

PRODUCTS = [
    {
        "name": "Самосвальный полуприцеп 32 м³",
        "price": 6_450_000,
        "label": True,
        "characteristics": {
            "Объём кузова": "32 м³",
            "Грузоподъёмность": "33 000 кг",
            "Количество осей": "3",
            "Тип подвески": "Пневматическая",
        },
    },
    {
        "name": "Бортовой полуприцеп 13,6 м",
        "price": 3_890_000,
        "label": True,
        "characteristics": {
            "Длина платформы": "13 600 мм",
            "Грузоподъёмность": "35 000 кг",
            "Количество осей": "3",
        },
    },
    {
        "name": "Изотермический фургон 3,5 т",
        "price": 4_120_000,
        "label": False,
        "characteristics": {
            "Полная масса": "3 500 кг",
            "Объём фургона": "18 м³",
            "Тип топлива": "Дизель",
        },
    },
    {
        "name": "Тентованный полуприцеп",
        "price": 3_250_000,
        "label": None,
        "characteristics": {
            "Объём кузова": "92 м³",
            "Количество осей": "3",
            "Тип тормозов": "Дисковые",
        },
    },
    {
        "name": "Низкорамный трал 40 т",
        "price": None,
        "label": False,
        "characteristics": {
            "Грузоподъёмность": "40 000 кг",
            "Высота погрузки": "900 мм",
            "Количество осей": "4",
        },
    },
]

NEWS = [
    "Поступление новых самосвальных полуприцепов",
    "Сезонные скидки на сервисное обслуживание",
    "Расширили склад запасных частей",
    "Открыли новую площадку для выдачи техники",
]

LOREM = (
    "Демонстрационный текст. Здесь в админке размещается описание: "
    "комплектация, условия поставки, сроки и другая информация для покупателя. "
    "Все данные на этой странице созданы командой seed и не относятся к реальной технике."
)


def _demo_image(name: str, color: str, size: tuple[int, int] = (860, 560)) -> UploadFile:
    """Картинка-заглушка с силуэтом грузовика: в репозитории нет чужих фото."""
    width, height = size
    image = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(image)
    ground = int(height * 0.72)
    draw.rectangle((0, ground, width, height), fill="#d9d9d9")
    # кузов, кабина, колёса
    draw.rectangle(
        (int(width * 0.12), int(height * 0.32), int(width * 0.68), ground - 20), fill="white"
    )
    draw.rectangle(
        (int(width * 0.70), int(height * 0.42), int(width * 0.88), ground - 20), fill="#f2f2f2"
    )
    draw.rectangle(
        (int(width * 0.74), int(height * 0.46), int(width * 0.85), int(height * 0.56)), fill=color
    )
    for x in (0.2, 0.32, 0.6, 0.8):
        cx, r = int(width * x), int(height * 0.07)
        draw.ellipse((cx - r, ground - 20 - r, cx + r, ground - 20 + r), fill="#222222")

    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=85)
    buffer.seek(0)
    return UploadFile(file=buffer, filename=name)


def _demo_logo() -> UploadFile:
    image = Image.new("RGB", (400, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((20, 20, 380, 380), radius=40, outline="black", width=16)
    draw.ellipse((110, 110, 290, 290), outline="black", width=24)
    draw.ellipse((170, 170, 230, 230), fill="black")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return UploadFile(file=buffer, filename="demo_logo.png")


async def seed() -> None:
    async with async_session_maker() as session:
        if await session.scalar(select(func.count()).select_from(MainContent)):
            raise SystemExit("В базе уже есть контент, наполнение пропущено")

        content = MainContent(
            logo=_demo_logo(),
            phone="8 800 000-00-00",
            email="info@example.com",
            header_title=settings.SITE_NAME,
            header_desc="Коммерческий транспорт и прицепная техника",
            main_desc="Демо-версия сайта: все товары и новости вымышленные",
            products_title="Техника в наличии и под заказ",
            about_us_title="О компании",
            about_us_desc=LOREM,
            news_title="Новости",
            brands_title="Бренды",
            address="г. Город, ул. Демонстрационная, 1",
            link_to_the_map="https://yandex.ru/maps/",
        )
        content.images.append(AboutUsImages(image_name=_demo_image("about_us.webp", "#2d4059")))
        session.add(content)

        session.add(
            TextPages(
                our_contacts="Телефон: 8 800 000-00-00\nПочта: info@example.com",
                delivery_and_payment="Доставка автовозом или своим ходом. "
                "Оплата по безналичному расчёту, лизинг.",
                privacy_policy="Демонстрационный текст политики конфиденциальности.",
                user_agreement="Демонстрационный текст пользовательского соглашения.",
            )
        )

        for index, item in enumerate(PRODUCTS, start=1):
            product = Products(
                name=item["name"],
                description=LOREM,
                price=item["price"],
                label=item["label"],
                is_active=True,
            )
            for photo in range(2):
                color = PALETTE[(index + photo) % len(PALETTE)]
                product.images.append(
                    ProductsImages(image_name=_demo_image(f"product_{index}_{photo}.webp", color))
                )
            for name, value in item["characteristics"].items():
                product.characteristics.append(
                    ProductsInfo(name_of_characteristic=name, value_of_characteristic=value)
                )
            session.add(product)

        today = date.today()
        for index, title in enumerate(NEWS, start=1):
            news = News(
                title=title,
                description=LOREM,
                date_of_the_news=today - timedelta(days=index * 9),
                is_active=True,
            )
            news.images.append(
                NewsImages(
                    news_image_name=_demo_image(
                        f"news_{index}.webp", PALETTE[index % len(PALETTE)], size=(768, 432)
                    )
                )
            )
            session.add(news)

        await session.commit()
    print("Демо-данные добавлены")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.commands")
    subparsers = parser.add_subparsers(dest="command", required=True)

    admin_parser = subparsers.add_parser("create-admin", help="создать администратора")
    admin_parser.add_argument("username")
    admin_parser.add_argument("--password", help="если не указан, будет запрошен")

    subparsers.add_parser("seed", help="наполнить пустую базу демо-данными")

    args = parser.parse_args()

    async def run() -> None:
        try:
            if args.command == "create-admin":
                password = args.password or getpass.getpass("Пароль: ")
                if not password:
                    raise SystemExit("Пароль не может быть пустым")
                await create_admin(args.username, password)
            elif args.command == "seed":
                await seed()
        finally:
            await engine.dispose()

    asyncio.run(run())


if __name__ == "__main__":
    main()
