from sqlalchemy import select

from app.dao.base import BaseDAO
from app.database import async_session_maker
from app.text_pages.models import TextPages
from app.text_pages.schemas import STextPages


class TextPagesDAO(BaseDAO):
    model = TextPages

    @classmethod
    async def get_pages(cls) -> STextPages | None:
        """Тексты страниц. Если записей несколько, берётся первая."""
        query = select(TextPages).order_by(TextPages.id).limit(1)
        async with async_session_maker() as session:
            pages = (await session.execute(query)).scalar_one_or_none()
        return STextPages.model_validate(pages) if pages else None
