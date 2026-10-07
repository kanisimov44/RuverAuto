from fastapi import APIRouter

from app.cache import cached
from app.text_pages.dao import TextPagesDAO
from app.text_pages.schemas import STextPages

router = APIRouter(
    prefix="/text_pages",
    tags=["Текстовые страницы"],
)


@router.get("", summary="Текстовые страницы")
@cached()
async def get_text_pages() -> STextPages | None:
    """Тексты страниц «Контакты», «Доставка и оплата» и юридических документов."""
    return await TextPagesDAO.get_pages()
