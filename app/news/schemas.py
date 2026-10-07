from datetime import date

from pydantic import BaseModel, ConfigDict


class SNewsAll(BaseModel):
    """Карточка новости в списке."""

    id: int
    title: str | None
    short_description: str | None
    date_of_the_news: date | None
    is_active: bool
    # Имена файлов в /static/uploads/
    images: list[str]

    model_config = ConfigDict(from_attributes=True)


class SNewsDetail(SNewsAll):
    """Страница новости."""

    description: str | None
