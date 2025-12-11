# ITMO MD 2025 - Crypto Data Pipeline

Система собирает цены криптовалют и новости, складывает их в MongoDB, переносит в PostgreSQL raw слой и готовит данные для аналитики через dbt.

## Modules
- `app/` — FastAPI сервис, собирает свечи Binance и новости Crypto.news, пишет в MongoDB (`binance_data`, `news_data`, `requests_log`).
- `airflow/` — DAGи `collect_data` (триггерит app) и `el_process` (Mongo -> Postgres raw). Стек Airflow 2.10.5 + LocalExecutor.
- `dwh/` — PostgreSQL 13 как витрина raw (`raw_binance_data`, `raw_news_data`).
- `dbt_project/` — структура dbt для стейджинга и витрин поверх raw.

## Data Flow
1. App эндпоинты `/api/binance/fetch-klines` и `/api/news/fetch-news` пишут данные в MongoDB.
2. Airflow `collect_data` вызывает эти эндпоинты по расписанию (каждый час).
3. Airflow `el_process` переносит новые документы в PostgreSQL (`raw.raw_binance_data`, `raw.raw_news_data`).
4. dbt использует raw таблицы, строит staging и marts для анализа влияния новостей.

## Layout
```
itmo-md-2025/
├── app/                 # FastAPI сервис (см. app/README.md)
│   ├── app/main.py
│   └── app/service/
├── airflow/             # Airflow + DAGи и utils
│   └── dags/{collect_data_dag.py, el_process_dag.py, utils/}
├── dwh/                 # PostgreSQL raw склад
├── dbt_project/         # README по структуре dbt
├── docker-compose.yaml  # включает compose из app, airflow, dwh
└── docs/                # материалы курса
```

## Quick Start
1. Требования: Docker + Docker Compose, Python 3.11+ (для локальной разработки app).
2. Создать env-файлы:
```
cp app/.env.example app/.env
cp dwh/.env.example dwh/.env
cp airflow/.env.example airflow/.env
```
3. Запуск стека:
```
docker-compose -f docker-compose.yaml up -d
```
4. Проверки:
- App: http://localhost:8000 (docs: /docs)
- Airflow: http://localhost:8080 (логин/пароль: airflow/airflow)
- PostgreSQL: порт 5433, БД `analytics`, пользователь/пароль `analytics`
- MongoDB: порт 27017, БД `crypto_data`

## Development
- Установить зависимости app: `cd app && uv sync`
- Запуск app локально: `uv run uvicorn app.main:app --reload`
- Пре-коммиты: `pip install pre-commit && pre-commit install`
- Проверка кодстайла: `pre-commit run --all-files`

## References
- `app/README.md`, `airflow/README.md`, `dwh/README.md`, `dbt_project/README.md`
- Отчёт по дз-1: `docs/hw1.md`
