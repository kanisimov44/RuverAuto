"""Страницы ошибок для посетителей сайта.

API, админка и статика отвечают на ошибки как обычно (JSON или ответ Starlette),
а страницы сайта получают HTML в общем оформлении.
"""

from fastapi import Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.logger import logger
from app.main_content.router import get_content
from app.news.router import get_all_news
from app.pages.router import render
from app.products.router import get_all_products
from app.text_pages.router import get_text_pages

NON_HTML_PREFIXES = ("/api", "/admin", "/static")

MESSAGES = {
    404: ("Страница не найдена", "Возможно, её удалили или в адресе есть опечатка."),
    500: ("Что-то пошло не так", "Мы уже знаем о проблеме. Попробуйте обновить страницу позже."),
}


def _wants_html(request: Request) -> bool:
    return not request.url.path.startswith(NON_HTML_PREFIXES)


async def _layout() -> dict:
    """Шапка и подвал для страницы ошибки. Если база недоступна, без них."""
    try:
        return {
            "content": await get_content(),
            "page": await get_text_pages(),
            "products": await get_all_products(),
            "all_news": await get_all_news(),
        }
    except Exception:
        logger.warning("Cannot load layout for error page", exc_info=True)
        return {"content": None, "page": None, "products": [], "all_news": []}


async def _render_error(request: Request, status_code: int):
    title, text = MESSAGES.get(status_code, ("Ошибка", "Не удалось обработать запрос."))
    return render(
        request,
        "pages/error.html",
        await _layout(),
        status_code=status_code,
        error_code=status_code,
        title=title,
        text=text,
    )


async def html_http_exception_handler(request: Request, exc: HTTPException):
    if _wants_html(request) and exc.status_code in (404, 500):
        return await _render_error(request, exc.status_code)
    return await http_exception_handler(request, exc)


async def html_validation_exception_handler(request: Request, exc: RequestValidationError):
    # /products/abc на сайте — это несуществующая страница, а не ошибка формата
    if _wants_html(request):
        return await _render_error(request, 404)
    return await request_validation_exception_handler(request, exc)


async def html_server_error_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", extra={"path": request.url.path}, exc_info=exc)
    if _wants_html(request):
        return await _render_error(request, 500)
    return JSONResponse({"detail": "Internal Server Error"}, status_code=500)
