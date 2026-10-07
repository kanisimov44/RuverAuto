from typing import Any, ClassVar

from fastapi import Request
from markupsafe import Markup, escape
from sqladmin import ModelView
from sqlalchemy import select
from wtforms import TextAreaField

from app.admin.columns import (
    column_labels_for_about_us_images,
    column_labels_for_main_content,
    column_labels_for_news,
    column_labels_for_news_images,
    column_labels_for_price_list,
    column_labels_for_producst_images,
    column_labels_for_products,
    column_labels_for_products_info,
    column_labels_for_text_pages,
    column_labels_for_users,
    form_column_for_main_content,
    form_column_for_news,
    form_column_for_price_list,
    form_column_for_users,
    form_columns_for_producst_images,
    form_columns_for_products,
)
from app.cache import clear_cache
from app.database import async_session_maker
from app.logger import logger
from app.main_content.models import AboutUsImages, MainContent
from app.news.models import News, NewsImages
from app.products.models import PriceList, Products, ProductsImages, ProductsInfo
from app.storages import file_name
from app.tasks.tasks import optimize_image
from app.text_pages.models import TextPages
from app.users.auth import get_password_hash
from app.users.models import Users


def _thumbnail_html(file: Any) -> Markup | str:
    name = file_name(file)
    if not name:
        return ""
    return Markup('<img src="/static/uploads/{}" alt="" style="height: 48px">').format(escape(name))


def thumbnail(field: str):
    """Форматтер колонки: миниатюра загруженного изображения вместо имени файла."""

    def formatter(model: Any, attribute: Any) -> Markup | str:
        return _thumbnail_html(getattr(model, field))

    return formatter


def related_thumbnails(field: str):
    """Форматтер колонки-связи с изображениями: миниатюра для каждой записи.

    sqladmin выводит такие колонки поэлементно, поэтому нужен список.
    """

    def formatter(model: Any, attribute: Any) -> list[Markup | str]:
        return [_thumbnail_html(getattr(image, field)) for image in model.images]

    return formatter


class BaseAdmin(ModelView):
    """Общее поведение разделов админки.

    После любого изменения сбрасывает кеш сайта, чтобы правки сразу были видны.
    Для полей из image_fields ставит в очередь Celery оптимизацию загруженных фото.
    """

    image_fields: ClassVar[tuple[str, ...]] = ()

    async def after_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        await clear_cache()
        uploaded = [
            field for field in self.image_fields if getattr(data.get(field), "filename", None)
        ]
        if uploaded:
            await self._schedule_image_optimization(model, uploaded)

    async def after_model_delete(self, model: Any, request: Request) -> None:
        await clear_cache()

    async def _schedule_image_optimization(self, model: Any, fields: list[str]) -> None:
        # Имя файла генерируется при сохранении (см. app/storages.py), а sqladmin
        # не перечитывает модель после коммита, поэтому берём его из БД.
        columns = [getattr(self.model, field) for field in fields]
        async with async_session_maker() as session:
            row = (await session.execute(select(*columns).filter_by(id=model.id))).one_or_none()

        for image in row or ():
            if not image:
                continue
            try:
                optimize_image.delay(image.path)
            except Exception:
                # Фото уже сохранено, без оптимизации сайт тоже работает
                logger.warning("Cannot schedule image optimization", exc_info=True)


class ProductsAdmin(BaseAdmin, model=Products):
    column_list = [
        Products.id,
        Products.name,
        Products.price,
        Products.label,
        Products.is_active,
        Products.characteristics,
        Products.description,
    ]

    name = "товар"
    name_plural = "Товары"
    icon = "fa-solid fa-car"
    column_formatters_detail = {"images": related_thumbnails("image_name")}

    column_labels = column_labels_for_products
    form_columns = form_columns_for_products

    form_overrides = {
        "description": TextAreaField,
    }


class ProductsImagesAdmin(BaseAdmin, model=ProductsImages):
    column_list = [c.name for c in ProductsImages.__table__.c] + [ProductsImages.product]
    name = "изображение товара"
    name_plural = "Изображения товаров"
    icon = "fa-solid fa-image"
    column_formatters = {"image_name": thumbnail("image_name")}
    column_formatters_detail = column_formatters

    column_labels = column_labels_for_producst_images
    form_columns = form_columns_for_producst_images

    image_fields = ("image_name",)


class ProductsInfoAdmin(BaseAdmin, model=ProductsInfo):
    column_list = [c.name for c in ProductsInfo.__table__.c] + [ProductsInfo.product]
    name = "характеристику товара"
    name_plural = "Характеристики товаров"
    icon = "fa-solid fa-star"

    column_labels = column_labels_for_products_info


class PriceListAdmin(BaseAdmin, model=PriceList):
    column_list = [c.name for c in PriceList.__table__.c]
    name = "прайс-лист"
    name_plural = "Прайс-листы"
    icon = "fa-solid fa-money-bill-1-wave"

    column_labels = column_labels_for_price_list
    form_columns = form_column_for_price_list


class MainContentAdmin(BaseAdmin, model=MainContent):
    column_list = [c.name for c in MainContent.__table__.c]
    name = "новую настройку"
    name_plural = "Настройка сайта"
    icon = "fa-solid fa-brush"
    column_formatters = {"logo": thumbnail("logo")}
    column_formatters_detail = {
        "logo": thumbnail("logo"),
        "images": related_thumbnails("image_name"),
    }
    can_delete = False

    column_labels = column_labels_for_main_content
    form_columns = form_column_for_main_content

    image_fields = ("logo",)
    form_overrides = {
        "main_desc": TextAreaField,
    }


class AboutUsAdmin(BaseAdmin, model=AboutUsImages):
    column_list = [c.name for c in AboutUsImages.__table__.c] + [AboutUsImages.about_us]
    name = "изображение «О нас»"
    name_plural = "Изображения «О нас»"
    icon = "fa-solid fa-image"
    column_formatters = {"image_name": thumbnail("image_name")}
    column_formatters_detail = column_formatters

    column_labels = column_labels_for_about_us_images

    image_fields = ("image_name",)


class TextPagesAdmin(BaseAdmin, model=TextPages):
    column_list = [c.name for c in TextPages.__table__.c]
    name = "текстовые страницы"
    name_plural = "Текстовые страницы"
    icon = "fa-solid fa-file-lines"
    can_delete = False

    column_labels = column_labels_for_text_pages

    form_overrides = {
        "our_contacts": TextAreaField,
        "delivery_and_payment": TextAreaField,
        "privacy_policy": TextAreaField,
        "user_agreement": TextAreaField,
    }


class UsersAdmin(BaseAdmin, model=Users):
    column_list = [Users.username, Users.is_active, Users.is_superuser, Users.role]
    name = "пользователя"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"
    can_delete = False

    column_labels = column_labels_for_users
    form_columns = form_column_for_users

    async def on_model_change(
        self, data: dict, model: Any, is_created: bool, request: Request
    ) -> None:
        # В форме редактирования поле заполнено текущим хешем. Если его не
        # трогали, повторное хеширование сделало бы пароль неверным.
        password = data.get("hashed_password")
        if password and (is_created or password != model.hashed_password):
            data["hashed_password"] = get_password_hash(password)
        return await super().on_model_change(data, model, is_created, request)


class NewsAdmin(BaseAdmin, model=News):
    column_list = [
        News.id,
        News.title,
        News.date_of_the_news,
        News.is_active,
        News.description,
    ]
    name = "новость"
    name_plural = "Новости"
    icon = "fa-solid fa-newspaper"
    column_formatters_detail = {"images": related_thumbnails("news_image_name")}
    can_delete = True

    column_labels = column_labels_for_news
    form_columns = form_column_for_news

    form_overrides = {"description": TextAreaField}


class NewsImagesAdmin(BaseAdmin, model=NewsImages):
    column_list = [c.name for c in NewsImages.__table__.c] + [NewsImages.the_news]
    name = "изображение новости"
    name_plural = "Изображения новостей"
    icon = "fa-solid fa-image"
    column_formatters = {"news_image_name": thumbnail("news_image_name")}
    column_formatters_detail = column_formatters

    column_labels = column_labels_for_news_images

    image_fields = ("news_image_name",)
