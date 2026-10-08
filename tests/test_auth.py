import jwt

from app.config import settings
from app.users.auth import (
    create_access_token,
    get_password_hash,
    get_user_by_token,
    verify_password,
)


def test_password_hash():
    hashed = get_password_hash("password")

    assert hashed != "password"
    assert verify_password("password", hashed)
    assert not verify_password("other", hashed)


async def test_token_roundtrip(ids):
    from app.users.dao import UserDAO

    admin = await UserDAO.find_one_or_none(username="admin")
    token = create_access_token({"sub": str(admin.id)})

    user = await get_user_by_token(token)
    assert user.username == "admin"


async def test_invalid_tokens():
    assert await get_user_by_token("not-a-token") is None

    foreign = jwt.encode(
        {"sub": "1"}, "another-secret-key-that-is-long-enough", algorithm=settings.ALGORITHM
    )
    assert await get_user_by_token(foreign) is None

    expired = jwt.encode({"sub": "1", "exp": 0}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert await get_user_by_token(expired) is None
