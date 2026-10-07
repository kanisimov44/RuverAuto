from pydantic import BaseModel, ConfigDict


class SMainContent(BaseModel):
    id: int
    # Имена файлов в /static/uploads/
    logo: str | None
    about_us_image: str | None
    phone: str | None
    email: str | None
    header_title: str | None
    header_desc: str | None
    main_desc: str | None
    products_title: str | None
    about_us_title: str | None
    about_us_desc: str | None
    news_title: str | None
    brands_title: str | None
    address: str | None
    link_to_the_map: str | None

    model_config = ConfigDict(from_attributes=True)
