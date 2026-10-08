from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
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


def format_date(value: date | None) -> str:
    return value.strftime("%d.%m.%Y") if value else ""


templates.env.filters["ru_date"] = format_date
templates.env.globals["site_name"] = settings.SITE_NAME
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


def render(request: Request, template: str, layout: dict[str, Any], **context: Any):
    return templates.TemplateResponse(request, template, {**layout, **context})


@router.get("/")
async def main_page(request: Request, layout: Layout):
    return render(request, "main.html", layout)


@router.get("/products")
async def products_page(request: Request, layout: Layout):
    price_list = await PriceListDAO.get_latest()
    return render(request, "products.html", layout, price_list=price_list)


@router.get("/products/{product_id}")
async def product_page(request: Request, layout: Layout, product=Depends(get_product_by_id)):
    return render(request, "product_detail.html", layout, product=product)


@router.get("/news")
async def news_page(request: Request, layout: Layout):
    return render(request, "news.html", layout)


@router.get("/news/{news_id}")
async def news_detail_page(request: Request, layout: Layout, news=Depends(get_news_by_id)):
    return render(request, "news_detail.html", layout, news=news)


@router.get("/delivery-and-payment")
async def delivery_and_payment_page(request: Request, layout: Layout):
    return render(request, "delivery_and_payment.html", layout)


@router.get("/our-contacts")
async def contacts_page(request: Request, layout: Layout):
    return render(request, "our_contacts.html", layout)


@router.get("/privacy-policy")
async def privacy_policy_page(request: Request, layout: Layout):
    return render(request, "privacy_policy.html", layout)


@router.get("/user-agreement")
async def user_agreement_page(request: Request, layout: Layout):
    return render(request, "user_agreement.html", layout)
