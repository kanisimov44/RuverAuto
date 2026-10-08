def truncate(text: str | None, length: int) -> str | None:
    """Обрезает текст до length символов и добавляет многоточие."""
    if not text:
        return text
    return text if len(text) <= length else text[:length] + "..."
