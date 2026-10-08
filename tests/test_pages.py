import json
import re

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app as fastapi_app
from app.pages.router import format_price, meta_text
from app.products.dao import ProductsDAO


@pytest.mark.parametrize(
    ("url", "title"),
    [
        ("/", "<title>Тестовая компания</title>"),
        ("/products", "<title>Товары - Тестовая компания</title>"),
        ("/news", "<title>Новости - Тестовая компания</title>"),
        ("/delivery-and-payment", "<title>Доставка и оплата - Тестовая компания</title>"),
        ("/our-contacts", "<title>Контакты - Тестовая компания</title>"),
        ("/privacy-policy", "<title>Политика конфиденциальности - Тестовая компания</title>"),
        ("/user-agreement", "<title>Пользовательское соглашение - Тестовая компания</title>"),
    ],
)
async def test_page_renders(client, url, title):
    response = await client.get(url)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert title in response.text
    # Копирайт в подвале берётся из SITE_NAME
    assert settings.SITE_NAME in response.text
    assert f"--accent: {settings.ACCENT_COLOR}" in response.text


async def test_text_page_content(client):
    response = await client.get("/our-contacts")

    assert "Контакты для теста" in response.text


async def test_main_page_shows_active_products_only(client):
    response = await client.get("/")

    assert "Самосвал" in response.text
    assert "Скрытый товар" not in response.text


async def test_menu_marks_current_section(client):
    response = await client.get("/products")

    assert 'href="/products" aria-current="page"' in response.text


async def test_product_page(client, ids):
    response = await client.get(f"/products/{ids['Самосвал']}")

    assert response.status_code == 200
    assert "/static/uploads/truck_2.webp" in response.text
    assert "Оси" in response.text
    assert "5 000 000 ₽" in response.text


async def test_product_without_price(client, ids):
    response = await client.get(f"/products/{ids['Фургон']}")

    assert "Цена по запросу" in response.text


async def test_product_page_seo(client, ids):
    response = await client.get(f"/products/{ids['Самосвал']}")
    html = response.text

    assert f'<link rel="canonical" href="http://test/products/{ids["Самосвал"]}">' in html
    assert '<meta property="og:type" content="product">' in html
    assert 'og:image" content="http://test/static/uploads/truck_1.webp"' in html

    ld_json = re.search(r'<script type="application/ld\+json">(.+?)</script>', html, re.S)
    data = json.loads(ld_json.group(1))
    assert data["@type"] == "Product"
    assert data["offers"]["price"] == 5_000_000
    assert data["offers"]["availability"] == "https://schema.org/InStock"


async def test_news_page_formats_dates(client):
    response = await client.get("/news")

    assert "20.05.2024" in response.text


@pytest.mark.parametrize("url", ["/products/999999", "/products/not-a-number", "/no-such-page"])
async def test_not_found_page(client, url):
    response = await client.get(url)

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("text/html")
    assert "Страница не найдена" in response.text
    assert '<meta name="robots" content="noindex">' in response.text


async def test_api_errors_stay_json(client):
    response = await client.get("/api/products/not-a-number")

    assert response.status_code == 422
    assert response.headers["content-type"] == "application/json"


async def test_server_error_page(monkeypatch):
    async def broken():
        raise RuntimeError("База недоступна")

    monkeypatch.setattr(ProductsDAO, "get_all_active", broken)
    transport = ASGITransport(app=fastapi_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        page = await client.get("/products")
        api = await client.get("/api/products")

    assert page.status_code == 500
    assert "Что-то пошло не так" in page.text
    assert api.status_code == 500
    assert api.json() == {"detail": "Internal Server Error"}


async def test_sitemap(client, ids):
    response = await client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    assert f"<loc>http://test/products/{ids['Самосвал']}</loc>" in response.text
    assert f"/products/{ids['Скрытый товар']}<" not in response.text
    assert "<lastmod>2024-05-20</lastmod>" in response.text
    assert "<loc>http://test/privacy-policy</loc>" in response.text


async def test_robots(client):
    response = await client.get("/robots.txt")

    assert "Disallow: /admin" in response.text
    assert "Sitemap: http://test/sitemap.xml" in response.text


def test_format_price():
    assert format_price(5_000_000) == "5 000 000 ₽"
    assert format_price(None) == ""


def test_meta_text():
    assert meta_text("  строка\nс переносом  ") == "строка с переносом"
    long_text = "слово " * 50
    result = meta_text(long_text, length=30)
    assert len(result) <= 30
    assert result.endswith("…")
