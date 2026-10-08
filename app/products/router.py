from pathlib import Path

from anyio import Path as AsyncPath
from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.cache import cached
from app.exceptions import PriceListNotFound, ProductNotFound
from app.products.dao import PriceListDAO, ProductsDAO
from app.products.schemas import SProductsAll, SProductsDetail

router = APIRouter(
    prefix="/products",
    tags=["Товары"],
)


@router.get("", summary="Список товаров")
@cached()
async def get_all_products() -> list[SProductsAll]:
    """Опубликованные товары."""
    return await ProductsDAO.get_all_active()


@router.get(
    "/price-list",
    summary="Скачать прайс-лист",
    response_class=FileResponse,
    responses={404: {"description": "Прайс-лист не загружен"}},
)
async def download_price_list():
    """Скачать актуальный прайс-лист."""
    price_list = await PriceListDAO.get_latest()
    if price_list is None or not await AsyncPath(price_list.file_name.path).is_file():
        raise PriceListNotFound

    extension = Path(price_list.file_name.name).suffix
    return FileResponse(
        path=price_list.file_name.path,
        filename=f"price_list{extension}",
        media_type="application/octet-stream",
    )


@router.get("/{product_id}", summary="Товар", responses={404: {"description": "Товар не найден"}})
@cached()
async def get_product_by_id(product_id: int) -> SProductsDetail:
    """Опубликованный товар с фото и характеристиками."""
    product = await ProductsDAO.get_active_by_id(product_id)
    if product is None:
        raise ProductNotFound
    return product
