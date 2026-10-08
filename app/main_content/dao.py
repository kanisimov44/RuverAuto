from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.main_content.models import MainContent
from app.main_content.schemas import SMainContent
from app.storages import file_name


class MainContentDAO(BaseDAO):
    model = MainContent

    @classmethod
    async def get_content(cls) -> SMainContent | None:
        """Настройки сайта. Если записей несколько, берётся первая."""
        query = (
            select(MainContent)
            .options(selectinload(MainContent.images))
            .order_by(MainContent.id)
            .limit(1)
        )
        async with async_session_maker() as session:
            content = (await session.execute(query)).scalar_one_or_none()

        if content is None:
            return None

        about_us_images = [image.image_name for image in content.images if image.image_name]
        return SMainContent(
            id=content.id,
            logo=file_name(content.logo),
            about_us_image=file_name(about_us_images[0]) if about_us_images else None,
            phone=content.phone,
            email=content.email,
            header_title=content.header_title,
            header_desc=content.header_desc,
            main_desc=content.main_desc,
            products_title=content.products_title,
            about_us_title=content.about_us_title,
            about_us_desc=content.about_us_desc,
            news_title=content.news_title,
            brands_title=content.brands_title,
            address=content.address,
            link_to_the_map=content.link_to_the_map,
        )
