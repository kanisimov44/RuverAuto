from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.news.models import News
from app.news.schemas import SNewsAll, SNewsDetail
from app.storages import file_name
from app.utils import truncate

SHORT_DESCRIPTION_LENGTH = 100


def _image_names(news: News) -> list[str]:
    return [name for image in news.images if (name := file_name(image.news_image_name))]


class NewsDAO(BaseDAO):
    model = News

    @classmethod
    async def get_all_active(cls) -> list[SNewsAll]:
        """Опубликованные новости, сначала свежие."""
        query = (
            select(News)
            .options(selectinload(News.images))
            .filter_by(is_active=True)
            .order_by(News.date_of_the_news.desc().nulls_last(), News.id.desc())
        )
        async with async_session_maker() as session:
            all_news = (await session.execute(query)).scalars().all()

        return [
            SNewsAll(
                id=news.id,
                title=news.title,
                short_description=truncate(news.description, SHORT_DESCRIPTION_LENGTH),
                date_of_the_news=news.date_of_the_news,
                is_active=news.is_active,
                images=_image_names(news),
            )
            for news in all_news
        ]

    @classmethod
    async def get_active_by_id(cls, news_id: int) -> SNewsDetail | None:
        query = (
            select(News).options(selectinload(News.images)).filter_by(id=news_id, is_active=True)
        )
        async with async_session_maker() as session:
            news = (await session.execute(query)).scalar_one_or_none()

        if news is None:
            return None

        return SNewsDetail(
            id=news.id,
            title=news.title,
            description=news.description,
            short_description=truncate(news.description, SHORT_DESCRIPTION_LENGTH),
            date_of_the_news=news.date_of_the_news,
            is_active=news.is_active,
            images=_image_names(news),
        )
