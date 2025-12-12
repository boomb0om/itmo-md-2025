# App Module

FastAPI сервис, который забирает свечи Binance и новости Crypto.news и складывает их в MongoDB (`binance_data`, `news_data`, `requests_log`).

## Structure
```
app/
├── app/main.py                  # FastAPI app + routers
├── app/api/{binance.py, news.py}
├── app/service/{binance_service.py, news_service.py}
├── app/core/{settings.py, logging.py}
├── app/database.py              # Подключение MongoDB
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Endpoints
- `GET /` — приветственное сообщение
- `GET /health` — пинг MongoDB
- `GET /api/binance/fetch-klines` — сбор свечей (параметры: `symbol`, `interval`, `limit`)
- `GET /api/news/fetch-news` — сбор новостей (параметры: `source`, `limit`)

## Run
Using Docker Compose (рекомендуется):
```
cd app
cp .env.example .env
docker-compose --env-file .env up -d
```

Local dev:
```
cd app
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload
```
