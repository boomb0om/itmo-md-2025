FROM ghcr.io/astral-sh/uv:python3.13-bookworm AS base

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS builder

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-project
COPY app ./app

FROM python:3.13-slim AS runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="${VIRTUAL_ENV}/bin:/usr/local/bin:${PATH}" \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=${VIRTUAL_ENV}
WORKDIR /app

COPY --from=base /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app
COPY pyproject.toml uv.lock ./

EXPOSE 8000

ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000

CMD uv run --no-sync uvicorn app.main:app --host ${APP_HOST} --port ${APP_PORT}
