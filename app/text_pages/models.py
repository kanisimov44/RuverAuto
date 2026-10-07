from sqlalchemy.orm import Mapped

from app.database import Base, intpk


class TextPages(Base):
    """Тексты отдельных страниц сайта. Запись одна."""

    __tablename__ = "text_pages"

    id: Mapped[intpk]
    our_contacts: Mapped[str | None]
    delivery_and_payment: Mapped[str | None]
    privacy_policy: Mapped[str | None]
    user_agreement: Mapped[str | None]

    def __str__(self):
        return "Текстовые страницы"
