from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, intpk
from app.storages import FileType, ImageType, file_name


class Products(Base):
    __tablename__ = "products"

    id: Mapped[intpk]
    name: Mapped[str | None]
    description: Mapped[str | None]
    price: Mapped[int | None]
    # True - "В наличии", False - "Под заказ", None - без лейбла
    label: Mapped[bool | None]
    is_active: Mapped[bool]

    characteristics: Mapped[list["ProductsInfo"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    images: Mapped[list["ProductsImages"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __str__(self):
        return f"Товар: {self.name}"


class ProductsImages(Base):
    __tablename__ = "products_images"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    image_name: Mapped[str | None] = mapped_column(ImageType())

    product: Mapped["Products"] = relationship(back_populates="images")

    def __str__(self):
        return f"Изображение: {file_name(self.image_name)}"


class ProductsInfo(Base):
    __tablename__ = "products_info"

    id: Mapped[intpk]
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    name_of_characteristic: Mapped[str]
    value_of_characteristic: Mapped[str]

    product: Mapped["Products"] = relationship(back_populates="characteristics")

    def __str__(self):
        return f"{self.name_of_characteristic}: {self.value_of_characteristic}"


class PriceList(Base):
    __tablename__ = "price_lists"

    id: Mapped[intpk]
    file_name: Mapped[str | None] = mapped_column(FileType())
    upload_data: Mapped[date | None] = mapped_column(Date)

    def __str__(self):
        return f"Прайс-лист от {self.upload_data}"
