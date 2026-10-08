import pytest
from pydantic import BaseModel
from redis.exceptions import ConnectionError as RedisConnectionError

from app import cache
from app.config import settings


class Item(BaseModel):
    id: int
    name: str


class FakeRedis:
    def __init__(self):
        self.storage: dict[str, bytes] = {}

    async def get(self, key):
        return self.storage.get(key)

    async def set(self, key, value, ex=None):
        self.storage[key] = value

    async def scan_iter(self, pattern):
        prefix = pattern.rstrip("*")
        for key in list(self.storage):
            if key.startswith(prefix):
                yield key

    async def delete(self, *keys):
        for key in keys:
            self.storage.pop(key, None)


class BrokenRedis:
    async def get(self, key):
        raise RedisConnectionError

    async def set(self, key, value, ex=None):
        raise RedisConnectionError


@pytest.fixture
def cache_enabled(monkeypatch):
    # В режиме TEST кеш отключён, здесь проверяем его самого
    monkeypatch.setattr(settings, "MODE", "DEV")


async def test_cached_returns_models_from_cache(monkeypatch, cache_enabled):
    monkeypatch.setattr(cache, "redis_client", FakeRedis())
    calls = []

    @cache.cached()
    async def get_items(item_id: int) -> list[Item]:
        calls.append(item_id)
        return [Item(id=item_id, name="first")]

    first = await get_items(item_id=1)
    second = await get_items(item_id=1)
    other = await get_items(item_id=2)

    assert calls == [1, 2]
    assert first == second == [Item(id=1, name="first")]
    assert isinstance(second[0], Item)
    assert other == [Item(id=2, name="first")]


async def test_clear_cache(monkeypatch, cache_enabled):
    fake = FakeRedis()
    monkeypatch.setattr(cache, "redis_client", fake)

    @cache.cached()
    async def get_item() -> Item:
        return Item(id=1, name="item")

    await get_item()
    fake.storage["celery-task-meta"] = b"not a cache key"
    await cache.clear_cache()

    assert list(fake.storage) == ["celery-task-meta"]


async def test_cached_works_without_redis(monkeypatch, cache_enabled):
    monkeypatch.setattr(cache, "redis_client", BrokenRedis())

    @cache.cached()
    async def get_item() -> Item:
        return Item(id=1, name="item")

    assert await get_item() == Item(id=1, name="item")
