from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi_storages import FileSystemStorage
from fastapi_storages.base import StorageFile
from fastapi_storages.integrations.sqlalchemy import FileType as BaseFileType
from fastapi_storages.integrations.sqlalchemy import ImageType as BaseImageType
from sqlalchemy.engine.interfaces import Dialect

# Изображения отдаются как статика: /static/uploads/<имя файла>
UPLOADS_DIR = Path("app/static/uploads")
# Прайс-листы отдаются только через эндпоинт скачивания
FILES_DIR = Path("app/files")


def unique_name(filename: str) -> str:
    """Случайное имя для загруженного файла с сохранением расширения.

    Исходное имя не используется: при нормализации из него вырезается кириллица
    («фото.jpg» превращается в «jpg»), а одинаковые имена перезаписывали бы
    файлы друг друга.
    """
    return f"{uuid4().hex}{Path(filename).suffix.lower()}"


class ImageType(BaseImageType):
    """Колонка с изображением. В БД хранится имя файла в UPLOADS_DIR."""

    cache_ok = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            *args, storage=FileSystemStorage(str(UPLOADS_DIR)), upload_to=unique_name, **kwargs
        )

    def process_result_value(self, value: Any, dialect: Dialect) -> StorageFile | None:
        # Базовая реализация открывает файл через PIL при каждом чтении из БД
        # и падает, если файла нет на диске. Размеры изображения нам не нужны.
        if value is None:
            return None
        return StorageFile(name=value, storage=self.storage)


class FileType(BaseFileType):
    """Колонка с файлом. В БД хранится имя файла в FILES_DIR."""

    cache_ok = True

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(
            *args, storage=FileSystemStorage(str(FILES_DIR)), upload_to=unique_name, **kwargs
        )


def file_name(file: StorageFile | str | None) -> str | None:
    """Имя файла без каталога: так его удобно подставлять в URL."""
    if not file:
        return None
    return Path(str(file)).name
