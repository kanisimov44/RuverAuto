from pathlib import Path

from app.database import async_session_maker
from app.products.models import PriceList
from app.storages import FILES_DIR


async def test_products_list_contains_only_active(client):
    response = await client.get("/api/products")

    assert response.status_code == 200
    names = [product["name"] for product in response.json()]
    assert names == ["Самосвал", "Фургон"]


async def test_products_list_item(client):
    truck = (await client.get("/api/products")).json()[0]

    assert truck["images"] == ["truck_1.webp", "truck_2.webp"]
    assert truck["label"] is True
    assert truck["short_description"].endswith("...")
    assert len(truck["short_description"]) == 53


async def test_product_detail(client, ids):
    response = await client.get(f"/api/products/{ids['Самосвал']}")

    assert response.status_code == 200
    product = response.json()
    assert product["name"] == "Самосвал"
    assert product["characteristics"] == [{"name": "Оси", "value": "3"}]


async def test_inactive_product_is_not_found(client, ids):
    response = await client.get(f"/api/products/{ids['Скрытый товар']}")

    assert response.status_code == 404


async def test_missing_product_is_not_found(client):
    response = await client.get("/api/products/999999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Товар не найден"}


async def test_news_sorted_from_newest(client):
    response = await client.get("/api/news")

    assert response.status_code == 200
    news = response.json()
    assert [item["title"] for item in news] == ["Свежая новость", "Старая новость"]
    assert news[0]["date_of_the_news"] == "2024-05-20"


async def test_news_detail(client, ids):
    response = await client.get(f"/api/news/{ids['Старая новость']}")

    assert response.status_code == 200
    assert response.json()["images"] == ["news_old.webp"]


async def test_draft_news_is_not_found(client, ids):
    response = await client.get(f"/api/news/{ids['Черновик']}")

    assert response.status_code == 404


async def test_main_content(client):
    response = await client.get("/api/main_content")

    assert response.status_code == 200
    content = response.json()
    assert content["logo"] == "logo.png"
    assert content["about_us_image"] == "about.webp"


async def test_text_pages(client):
    response = await client.get("/api/text_pages")

    assert response.status_code == 200
    assert response.json()["our_contacts"] == "Контакты для теста"


async def test_price_list_download(client):
    response = await client.get("/api/products/price-list")
    assert response.status_code == 404

    stored_name = "test_price.xlsx"
    path = Path(FILES_DIR) / stored_name
    path.write_bytes(b"price list")
    async with async_session_maker() as session:
        price_list = PriceList(file_name=stored_name)
        session.add(price_list)
        await session.commit()

    try:
        response = await client.get("/api/products/price-list")
        assert response.status_code == 200
        assert response.content == b"price list"
        assert 'filename="price_list.xlsx"' in response.headers["content-disposition"]
    finally:
        path.unlink()
        async with async_session_maker() as session:
            await session.delete(price_list)
            await session.commit()
