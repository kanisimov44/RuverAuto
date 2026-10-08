from datetime import date

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, intpk
from app.storages import ImageType, file_name


class News(Base):
    __tablename__ = "news"

    id: Mapped[intpk]
    title: Mapped[str | None]
    description: Mapped[str | None]
    date_of_the_news: Mapped[date | None] = mapped_column(Date)
    is_active: Mapped[bool]

    images: Mapped[list["NewsImages"]] = relationship(
        back_populates="the_news",
        cascade="all, delete-orphan",
    )

    def __str__(self):
        return f"Новость: {self.title}"


class NewsImages(Base):
    __tablename__ = "news_images"

    id: Mapped[intpk]
    news_id: Mapped[int] = mapped_column(ForeignKey("news.id", ondelete="CASCADE"))
    news_image_name: Mapped[str | None] = mapped_column(ImageType())

    the_news: Mapped["News"] = relationship(back_populates="images")

    def __str__(self):
        return f"Изображение: {file_name(self.news_image_name)}"
