from PIL import Image

from app.storages import file_name, unique_name
from app.tasks.tasks import MAX_IMAGE_SIZE, optimize_image
from app.utils import truncate


def test_truncate():
    assert truncate(None, 5) is None
    assert truncate("short", 5) == "short"
    assert truncate("long text", 4) == "long..."


def test_unique_name_keeps_extension():
    first = unique_name("Фото грузовика.JPG")
    second = unique_name("Фото грузовика.JPG")

    assert first != second
    assert first.endswith(".jpg")
    assert first.isascii()


def test_file_name():
    assert file_name("app/static/uploads/photo.webp") == "photo.webp"
    assert file_name(None) is None


def test_optimize_image_resizes_large_photo(tmp_path):
    path = tmp_path / "photo.jpg"
    Image.new("RGB", (4000, 2000), "red").save(path, "JPEG")

    optimize_image(str(path))

    with Image.open(path) as image:
        assert image.size == (MAX_IMAGE_SIZE[0], MAX_IMAGE_SIZE[0] // 2)
        assert image.format == "JPEG"


def test_optimize_image_keeps_small_photo(tmp_path):
    path = tmp_path / "photo.png"
    Image.new("RGBA", (300, 200), "blue").save(path, "PNG")

    optimize_image(str(path))

    with Image.open(path) as image:
        assert image.size == (300, 200)


def test_optimize_image_missing_file(tmp_path):
    optimize_image(str(tmp_path / "missing.jpg"))
