from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, Response
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.main_content.router import get_content
from app.news.router import get_all_news, get_news_by_id
from app.products.dao import PriceListDAO
from app.products.router import get_all_products, get_product_by_id
from app.text_pages.router import get_text_pages

router = APIRouter(
    tags=["Страницы сайта"],
    default_response_class=HTMLResponse,
    include_in_schema=False,
)

templates = Jinja2Templates(directory="app/templates")

META_DESCRIPTION_LENGTH = 160


def format_date(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


def format_price(value: int | None) -> str:
    """5000000 -> '5 000 000 ₽' с неразрывными пробелами."""
    if value is None:
        return ""
    return f"{value:,}".replace(",", " ") + " ₽"


def meta_text(value: str | None, length: int = META_DESCRIPTION_LENGTH) -> str:
    """Текст для meta description: одна строка, не длиннее length символов."""
    text = " ".join((value or "").split())
    if len(text) <= length:
        return text
    return text[: length - 1].rsplit(" ", 1)[0] + "…"


templates.env.filters["ru_date"] = format_date
templates.env.filters["rub"] = format_price
templates.env.filters["meta"] = meta_text
templates.env.globals["site_name"] = settings.SITE_NAME
templates.env.globals["accent_color"] = settings.ACCENT_COLOR
templates.env.globals["current_year"] = lambda: date.today().year


async def get_layout_context(
    content=Depends(get_content),
    page=Depends(get_text_pages),
    products=Depends(get_all_products),
    all_news=Depends(get_all_news),
) -> dict[str, Any]:
    """Данные, которые нужны base.html на любой странице: шапка, меню, подвал."""
    return {
        "content": content,
        "page": page,
        "products": products,
        "all_news": all_news,
    }


Layout = Annotated[dict[str, Any], Depends(get_layout_context)]


def render(
    request: Request,
    template: str,
    layout: dict[str, Any],
    status_code: int = 200,
    **context: Any,
):
    canonical_url = str(request.url.replace(query="", fragment=""))
    content = layout.get("content")
    # Название в шапке: из настроек сайта в админке, иначе SITE_NAME
    brand = (content.header_title if content else None) or settings.SITE_NAME
    return templates.TemplateResponse(
        request,
        template,
        {**layout, "brand": brand, "canonical_url": canonical_url, **context},
        status_code=status_code,
    )


@router.get("/")
async def main_page(request: Request, layout: Layout):
    return render(request, "pages/index.html", layout)


@router.get("/products")
async def products_page(request: Request, layout: Layout):
    price_list = await PriceListDAO.get_latest()
    return render(request, "pages/products.html", layout, price_list=price_list)


@router.get("/products/{product_id}")
async def product_page(request: Request, layout: Layout, product=Depends(get_product_by_id)):
    return render(request, "pages/product.html", layout, product=product)


@router.get("/news")
async def news_page(request: Request, layout: Layout):
    return render(request, "pages/news.html", layout)


@router.get("/news/{news_id}")
async def news_detail_page(request: Request, layout: Layout, news=Depends(get_news_by_id)):
    return render(request, "pages/news_item.html", layout, news=news)


# Текстовые страницы: адрес -> (заголовок, поле в TextPages)
TEXT_PAGES = {
    "/delivery-and-payment": ("Доставка и оплата", "delivery_and_payment"),
    "/our-contacts": ("Контакты", "our_contacts"),
    "/privacy-policy": ("Политика конфиденциальности", "privacy_policy"),
    "/user-agreement": ("Пользовательское соглашение", "user_agreement"),
}


def _text_page_handler(title: str, field: str):
    async def handler(request: Request, layout: Layout):
        text = getattr(layout["page"], field, None) if layout["page"] else None
        return render(request, "pages/text_page.html", layout, title=title, text=text)

    handler.__name__ = f"{field}_page"
    return handler


for path, (title, field) in TEXT_PAGES.items():
    router.add_api_route(path, _text_page_handler(title, field), methods=["GET"])


@router.get("/sitemap.xml")
async def sitemap(
    request: Request,
    products=Depends(get_all_products),
    all_news=Depends(get_all_news),
    page=Depends(get_text_pages),
):
    base_url = str(request.base_url).rstrip("/")
    text_pages = [
        path for path, (_, field) in TEXT_PAGES.items() if page and getattr(page, field, None)
    ]
    xml = templates.get_template("sitemap.xml").render(
        base_url=base_url,
        products=products,
        all_news=all_news,
        text_pages=text_pages,
    )
    return Response(xml, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    base_url = str(request.base_url).rstrip("/")
    return f"User-agent: *\nDisallow: /admin\nDisallow: /api\nSitemap: {base_url}/sitemap.xml\n"
