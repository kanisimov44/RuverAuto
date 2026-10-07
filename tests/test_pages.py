import pytest


@pytest.mark.parametrize(
    "url",
    [
        "/",
        "/products",
        "/news",
        "/delivery-and-payment",
        "/our-contacts",
        "/privacy-policy",
        "/user-agreement",
    ],
)
async def test_page_renders(client, url):
    response = await client.get(url)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    # Шапка из настроек сайта есть на любой странице
    assert "Рувер-Авто" in response.text


async def test_main_page_shows_active_products_only(client):
    response = await client.get("/")

    assert "Самосвал" in response.text
    assert "Скрытый товар" not in response.text


async def test_product_page(client, ids):
    response = await client.get(f"/products/{ids['Самосвал']}")

    assert response.status_code == 200
    assert "/static/uploads/truck_2.webp" in response.text
    assert "Оси" in response.text


async def test_news_page_formats_dates(client):
    response = await client.get("/news")

    assert "20.05.2024" in response.text


async def test_missing_product_page(client):
    response = await client.get("/products/999999")

    assert response.status_code == 404
