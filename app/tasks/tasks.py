from pathlib import Path

from PIL import Image, ImageOps

from app.logger import logger
from app.tasks.celery_app import celery_app

# Фото больше этого размера уменьшаются с сохранением пропорций
MAX_IMAGE_SIZE = (1920, 1920)
QUALITY = 85


@celery_app.task
def optimize_image(path: str) -> None:
    """Уменьшает загруженное через админку изображение и пережимает его.

    Файл перезаписывается на месте под тем же именем, поэтому запись в БД
    обновлять не нужно. Поворот из EXIF применяется к пикселям, иначе после
    удаления метаданных фото с телефона может оказаться повёрнутым.
    """
    image_path = Path(path)
    if not image_path.is_file():
        logger.warning("Image for optimization not found", extra={"path": path})
        return

    with Image.open(image_path) as original:
        image_format = original.format
        image = ImageOps.exif_transpose(original)
        image.thumbnail(MAX_IMAGE_SIZE)

    save_params = {"optimize": True}
    if image_format in ("JPEG", "WEBP"):
        save_params["quality"] = QUALITY
    image.save(image_path, format=image_format, **save_params)

    logger.info("Image optimized", extra={"path": path, "size": image.size})
