from enum import Enum as PyEnum

from sqlalchemy import Enum
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, intpk


class Roles(PyEnum):
    ROOT = "root"
    ADMIN = "admin"
    USER = "user"


# Роли, которым разрешён вход в админку
ADMIN_ROLES = (Roles.ROOT, Roles.ADMIN)


class Users(Base):
    __tablename__ = "users"

    id: Mapped[intpk]
    username: Mapped[str] = mapped_column(unique=True)
    hashed_password: Mapped[str]
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    role: Mapped[Roles] = mapped_column(Enum(Roles), default=Roles.USER)

    def __str__(self):
        return f"Пользователь {self.username}"
