FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /ruverauto

# Зависимости ставятся отдельным слоем, чтобы правки кода не пересобирали его.
# INSTALL_DEV=1 добавляет dev-зависимости (тесты, линтер) - для CI.
ARG INSTALL_DEV=0
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$INSTALL_DEV" = "1" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi

RUN useradd --create-home --uid 1000 app
COPY --chown=app:app . .
# Каталоги загрузок создаются заранее: тогда тома docker получат права пользователя app
RUN mkdir -p app/static/uploads app/files && chown app:app app/static/uploads app/files

USER app
EXPOSE 8000

CMD ["gunicorn", "app.main:app", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--forwarded-allow-ips", "*"]
