"""Кеширование ответов в Redis.

Кешируются функции чтения публичного контента. Результат сериализуется через
pydantic по аннотации возвращаемого типа и при чтении восстанавливается в те же
модели, поэтому шаблоны получают одинаковые объекты с кешем и без него.

Любое изменение в админке сбрасывает кеш целиком (см. app/admin/views.py):
контента на сайте немного, а точечная инвалидация усложнила бы код.

Если Redis недоступен, функции выполняются напрямую — сайт продолжает работать.
"""

import functools
from collections.abc import Awaitable, Callable
from typing import Any, ParamSpec, TypeVar, get_type_hints

from pydantic import TypeAdapter
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.config import settings
from app.logger import logger

KEY_PREFIX = "cache:"

P = ParamSpec("P")
R = TypeVar("R")

redis_client = Redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)


def _make_key(func: Callable[..., Any], kwargs: dict[str, Any]) -> str:
    params = ":".join(f"{name}={value}" for name, value in sorted(kwargs.items()))
    return f"{KEY_PREFIX}{func.__module__}.{func.__qualname__}:{params}"


def cached(
    expire: int | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Кеширует результат асинхронной функции в Redis.

    Аргументы функции должны передаваться по имени: так их передаёт FastAPI,
    и из них строится ключ кеша.
    """

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        adapter = TypeAdapter(get_type_hints(func)["return"])

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if settings.MODE == "TEST" or args:
                return await func(*args, **kwargs)

            key = _make_key(func, kwargs)
            try:
                raw = await redis_client.get(key)
            except RedisError:
                logger.warning("Redis is unavailable, cache skipped", exc_info=True)
                return await func(*args, **kwargs)

            if raw is not None:
                return adapter.validate_json(raw)

            result = await func(*args, **kwargs)
            try:
                await redis_client.set(
                    key,
                    adapter.dump_json(result),
                    ex=expire or settings.CACHE_EXPIRE_SECONDS,
                )
            except RedisError:
                logger.warning("Cannot save value to cache", exc_info=True)
            return result

        return wrapper

    return decorator


async def clear_cache() -> None:
    """Удаляет все закешированные значения."""
    try:
        keys = [key async for key in redis_client.scan_iter(f"{KEY_PREFIX}*")]
        if keys:
            await redis_client.delete(*keys)
    except RedisError:
        logger.warning("Cannot clear cache", exc_info=True)
