from fastapi import APIRouter

from app.cache import cached
from app.main_content.dao import MainContentDAO
from app.main_content.schemas import SMainContent

router = APIRouter(
    prefix="/main_content",
    tags=["Контент"],
)


@router.get("", summary="Настройки сайта")
@cached()
async def get_content() -> SMainContent | None:
    """Настройки сайта: шапка, подвал, контакты, тексты главной."""
    return await MainContentDAO.get_content()
