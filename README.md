# ITMO MD 2025 - Crypto Data Pipeline

Система собирает цены криптовалют и новости, складывает их в MongoDB, переносит в PostgreSQL raw слой и готовит данные для аналитики через dbt.

## Modules
- `app/` — FastAPI сервис, собирает свечи Binance и новости Crypto.news, пишет в MongoDB (`binance_data`, `news_data`, `requests_log`).
- `airflow/` — DAGи:
  - `collect_data` - вызывает эндпоинты app для сбора данных
  - `el_process` - переносит данные из MongoDB в PostgreSQL raw слой
  - `dbt_transformation` - запускает dbt модели (STG → ODS → DM) каждые 6 часов
  - Стек: Airflow 2.10.5 + LocalExecutor + dbt + Elementary
- `dwh/` — PostgreSQL 13 как хранилище данных (raw, stg, ods, dm схемы).
- `dbt_project/` — dbt проект с моделями трансформации:
  - STG (staging): распаковка JSONB, инкрементальная загрузка (delete+insert)
  - ODS (operational data store): агрегация и обогащение (merge)
  - DM (data marts): аналитические витрины (table)
  - Тесты: 4 типа dbt-core + 6 типов Elementary
  - Документация моделей и источников

## Data Flow
1. App эндпоинты `/api/binance/fetch-klines` и `/api/news/fetch-news` пишут данные в MongoDB.
2. Airflow `collect_data` вызывает эти эндпоинты по расписанию (каждый час).
3. Airflow `el_process` переносит новые документы в PostgreSQL (`raw.raw_binance_data`, `raw.raw_news_data`) каждые 6 часов.
4. Airflow `dbt_transformation` запускает dbt модели каждые 6 часов:
   - **STG layer**: Распаковка JSONB → `stg.stg_binance_klines`, `stg.stg_news_articles`
   - **ODS layer**: Агрегация и обогащение → `ods.ods_binance_daily_agg`, `ods.ods_news_enriched`
   - **DM layer**: Аналитические витрины → `dm.dm_crypto_market_overview`, `dm.dm_news_impact_analysis`
5. Elementary генерирует отчёт с результатами тестов и мониторинга качества данных.

## Layout
```
itmo-md-2025/
├── app/                         # FastAPI сервис (см. app/README.md)
│   ├── app/main.py
│   └── app/service/
├── airflow/                     # Airflow + DAGи и utils
│   ├── dags/
│   │   ├── collect_data_dag.py      # Сбор данных через app
│   │   ├── el_process_dag.py        # MongoDB → PostgreSQL raw
│   │   ├── dbt_transformation_dag.py # dbt трансформации
│   │   └── utils/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt         # включает dbt + elementary
├── dwh/                         # PostgreSQL хранилище
├── dbt_project/                 # DBT проект (см. dbt_project/README.md)
│   ├── models/
│   │   ├── sources.yml         # raw источники
│   │   ├── stg/                # Staging models
│   │   ├── ods/                # ODS models
│   │   └── dm/                 # Data Mart models
│   ├── macros/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml            # Elementary
│   └── requirements.txt
├── docker-compose.yaml          # главный compose
└── docs/                        # материалы курса
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

## DBT Analytics

### Витрины данных
После запуска dbt доступны следующие аналитические витрины:

1. **dm.dm_crypto_market_overview** - обзор крипторынка:
   - Текущие цены и объёмы
   - Moving averages (7d, 30d)
   - Волатильность
   - Индикаторы тренда

2. **dm.dm_news_impact_analysis** - анализ влияния новостей:
   - Sentiment анализ новостей (positive/negative/neutral)
   - Корреляция sentiment с изменениями цен
   - Ежедневные метрики новостей

### Запуск dbt локально

```bash
cd dbt_project
cp .env.example .env
# отредактировать .env с параметрами подключения к PostgreSQL

# Установить зависимости
pip install -r requirements.txt
dbt deps --profiles-dir .

# Запустить модели
dbt run --profiles-dir .

# Запустить тесты
dbt test --profiles-dir .

# Сгенерировать Elementary отчёт
edr report --profiles-dir .
# Отчёт будет в ./edr_target/elementary_report.html
```

## Тестирование и качество данных

Проект использует:
- **4 типа dbt-core тестов**: unique, not_null, accepted_values, relationships
- **6 типов Elementary тестов**: volume_anomalies, freshness_anomalies, column_anomalies, и др.
- **Window functions** в SQL для расчёта moving averages и агрегаций
- **CTE (Common Table Expressions)** во всех DM моделях
- **2 стратегии инкрементальной загрузки**: delete+insert (STG) и merge (ODS)

## References
- `app/README.md` - описание FastAPI сервиса
- `airflow/README.md` - описание DAG'ов
- `dwh/README.md` - структура БД
- `dbt_project/README.md` - **подробное описание dbt проекта, моделей, тестов**
- `docs/hw1.md` - отчёт по дз-1
