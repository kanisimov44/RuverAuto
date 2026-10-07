from fastapi import HTTPException, status


class DefaultException(HTTPException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail = ""

    def __init__(self):
        super().__init__(status_code=self.status_code, detail=self.detail)


class ProductNotFound(DefaultException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Товар не найден"


class NewsNotFound(DefaultException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Новость не найдена"


class PriceListNotFound(DefaultException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Прайс-лист не загружен"
