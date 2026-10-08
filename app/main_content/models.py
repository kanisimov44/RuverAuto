from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, intpk
from app.storages import ImageType, file_name


class MainContent(Base):
    """Настройки сайта: шапка, подвал, контакты и тексты главной. Запись одна."""

    __tablename__ = "main_content"

    id: Mapped[intpk]
    logo: Mapped[str | None] = mapped_column(ImageType())
    phone: Mapped[str | None]
    email: Mapped[str | None]
    header_title: Mapped[str | None]
    header_desc: Mapped[str | None]
    main_desc: Mapped[str | None]
    products_title: Mapped[str | None]
    about_us_title: Mapped[str | None]
    about_us_desc: Mapped[str | None]
    news_title: Mapped[str | None]
    brands_title: Mapped[str | None]
    address: Mapped[str | None]
    link_to_the_map: Mapped[str | None]

    images: Mapped[list["AboutUsImages"]] = relationship(
        back_populates="about_us",
        cascade="all, delete-orphan",
    )

    def __str__(self):
        return f"Контент: {self.about_us_title}"


class AboutUsImages(Base):
    __tablename__ = "about_us_images"

    id: Mapped[intpk]
    about_us_id: Mapped[int] = mapped_column(ForeignKey("main_content.id", ondelete="CASCADE"))
    image_name: Mapped[str | None] = mapped_column(ImageType())

    about_us: Mapped["MainContent"] = relationship(back_populates="images")

    def __str__(self):
        return f"Изображение: {file_name(self.image_name)}"
