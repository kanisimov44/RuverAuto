from fastapi import APIRouter

from app.cache import cached
from app.exceptions import NewsNotFound
from app.news.dao import NewsDAO
from app.news.schemas import SNewsAll, SNewsDetail

router = APIRouter(
    prefix="/news",
    tags=["Новости"],
)


@router.get("", summary="Список новостей")
@cached()
async def get_all_news() -> list[SNewsAll]:
    """Опубликованные новости, сначала свежие."""
    return await NewsDAO.get_all_active()


@router.get("/{news_id}", summary="Новость", responses={404: {"description": "Новость не найдена"}})
@cached()
async def get_news_by_id(news_id: int) -> SNewsDetail:
    """Опубликованная новость с фото."""
    news = await NewsDAO.get_active_by_id(news_id)
    if news is None:
        raise NewsNotFound
    return news
