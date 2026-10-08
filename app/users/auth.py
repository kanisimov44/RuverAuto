from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.config import settings
from app.users.dao import UserDAO


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def authenticate_user(username: str, password: str):
    """Возвращает пользователя, если логин и пароль верны, иначе None."""
    user = await UserDAO.find_one_or_none(username=username)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


async def get_user_by_token(token: str):
    """Возвращает пользователя по JWT. Если токен невалиден или истёк - None."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.InvalidTokenError:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None
    return await UserDAO.find_one_or_none(id=int(user_id))
