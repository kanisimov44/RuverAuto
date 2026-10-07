from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.config import settings
from app.users.auth import authenticate_user, create_access_token, get_user_by_token
from app.users.models import ADMIN_ROLES


def _can_use_admin(user) -> bool:
    return bool(user and user.is_active and user.role in ADMIN_ROLES)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        user = await authenticate_user(str(form["username"]), str(form["password"]))
        if not _can_use_admin(user):
            return False

        request.session.update({"token": create_access_token({"sub": str(user.id)})})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")
        if not token:
            return False

        user = await get_user_by_token(token)
        return _can_use_admin(user)


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
