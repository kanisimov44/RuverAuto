from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.products.models import PriceList, Products
from app.products.schemas import SCharacteristic, SProductsAll, SProductsDetail
from app.storages import file_name
from app.utils import truncate

SHORT_DESCRIPTION_LENGTH = 50


def _image_names(product: Products) -> list[str]:
    return [name for image in product.images if (name := file_name(image.image_name))]


class ProductsDAO(BaseDAO):
    model = Products

    @classmethod
    async def get_all_active(cls) -> list[SProductsAll]:
        query = (
            select(Products)
            .options(selectinload(Products.images))
            .filter_by(is_active=True)
            .order_by(Products.id)
        )
        async with async_session_maker() as session:
            products = (await session.execute(query)).scalars().all()

        return [
            SProductsAll(
                id=product.id,
                name=product.name,
                short_description=truncate(product.description, SHORT_DESCRIPTION_LENGTH),
                price=product.price,
                label=product.label,
                is_active=product.is_active,
                images=_image_names(product),
            )
            for product in products
        ]

    @classmethod
    async def get_active_by_id(cls, product_id: int) -> SProductsDetail | None:
        query = (
            select(Products)
            .options(selectinload(Products.images), selectinload(Products.characteristics))
            .filter_by(id=product_id, is_active=True)
        )
        async with async_session_maker() as session:
            product = (await session.execute(query)).scalar_one_or_none()

        if product is None:
            return None

        return SProductsDetail(
            id=product.id,
            name=product.name,
            description=product.description,
            short_description=truncate(product.description, SHORT_DESCRIPTION_LENGTH),
            price=product.price,
            label=product.label,
            is_active=product.is_active,
            images=_image_names(product),
            characteristics=[
                SCharacteristic(
                    name=char.name_of_characteristic,
                    value=char.value_of_characteristic,
                )
                for char in product.characteristics
            ],
        )


class PriceListDAO(BaseDAO):
    model = PriceList

    @classmethod
    async def get_latest(cls) -> PriceList | None:
        """Последний загруженный прайс-лист с файлом."""
        query = (
            select(PriceList)
            .where(PriceList.file_name.is_not(None))
            .order_by(PriceList.upload_data.desc().nulls_last(), PriceList.id.desc())
            .limit(1)
        )
        async with async_session_maker() as session:
            return (await session.execute(query)).scalar_one_or_none()
