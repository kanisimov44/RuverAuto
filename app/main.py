import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from sqladmin.i18n import I18nConfig
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.admin.auth import authentication_backend
from app.admin.views import (
    AboutUsAdmin,
    MainContentAdmin,
    NewsAdmin,
    NewsImagesAdmin,
    PriceListAdmin,
    ProductsAdmin,
    ProductsImagesAdmin,
    ProductsInfoAdmin,
    TextPagesAdmin,
    UsersAdmin,
)
from app.cache import redis_client
from app.config import settings
from app.database import engine
from app.logger import logger
from app.main_content.router import router as content_router
from app.news.router import router as news_router
from app.pages.router import router as pages_router
from app.products.router import router as products_router
from app.storages import UPLOADS_DIR
from app.text_pages.router import router as text_pages_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await redis_client.aclose()
    await engine.dispose()


app = FastAPI(
    title=settings.SITE_NAME,
    version="1.0.0",
    description="Сайт компании: страницы, JSON API и админка.",
    lifespan=lifespan,
)

# За nginx: корректные схема и адрес клиента из X-Forwarded-* заголовков
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

api_router = APIRouter(prefix="/api")
api_router.include_router(products_router)
api_router.include_router(news_router)
api_router.include_router(content_router)
api_router.include_router(text_pages_router)

app.include_router(api_router)
app.include_router(pages_router)

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

admin = Admin(
    app,
    engine,
    authentication_backend=authentication_backend,
    title=settings.SITE_NAME,
    favicon_url="/static/img/favicon.png",
    i18n_config=I18nConfig(default_locale="ru"),
)
admin.add_view(MainContentAdmin)
admin.add_view(AboutUsAdmin)
admin.add_view(ProductsAdmin)
admin.add_view(ProductsInfoAdmin)
admin.add_view(ProductsImagesAdmin)
admin.add_view(PriceListAdmin)
admin.add_view(NewsAdmin)
admin.add_view(NewsImagesAdmin)
admin.add_view(TextPagesAdmin)
admin.add_view(UsersAdmin)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    logger.info(
        "Request handled",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(time.perf_counter() - start_time, 4),
        },
    )
    return response
