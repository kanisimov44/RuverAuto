from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения. Читаются из переменных окружения и файла .env.

    Переменные POSTGRES_* общие для приложения и контейнера postgres:
    образ postgres создаёт по ним пользователя и базу при первом запуске.
    """

    model_config = SettingsConfigDict(env_file=".env")

    MODE: Literal["DEV", "TEST", "PROD"] = "DEV"
    LOG_LEVEL: str = "INFO"

    # Название компании: заголовок вкладки, копирайт, админка, документация API
    SITE_NAME: str = "Моя компания"
    # Домен сайта: на него настраивается nginx в продакшен-режиме
    DOMAIN: str = "localhost"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    CACHE_EXPIRE_SECONDS: int = 60

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


settings = Settings()
