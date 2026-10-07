from pydantic import BaseModel, ConfigDict


class SCharacteristic(BaseModel):
    name: str
    value: str


class SProductsAll(BaseModel):
    """Карточка товара в списке."""

    id: int
    name: str | None
    short_description: str | None
    price: int | None
    label: bool | None
    is_active: bool
    # Имена файлов в /static/uploads/
    images: list[str]

    model_config = ConfigDict(from_attributes=True)


class SProductsDetail(SProductsAll):
    """Страница товара."""

    description: str | None
    characteristics: list[SCharacteristic]
