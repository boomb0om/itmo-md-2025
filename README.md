# ITMO MD 2025 - Crypto Data Pipeline

Полноценный data pipeline для сбора, хранения и аналитики криптовалютных данных.

**Стек**: Python (FastAPI + MongoDB) → Airflow → PostgreSQL → DBT → Elementary

## Архитектура

```
┌─────────────┐
│   Binance   │ ──┐
│ Crypto.news │   │
└─────────────┘   │
                  ▼
        ┌──────────────────┐
        │  FastAPI App     │  Сбор данных
        │  (app/)          │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │    MongoDB       │  Временное хранилище
        │  (binance_data,  │
        │   news_data)     │
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  Airflow EL DAG  │  Перенос в DWH
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  PostgreSQL 13   │  Data Warehouse
        │  raw schema      │  (raw_binance_data,
        │  (JSONB)         │   raw_news_data)
        └────────┬─────────┘
                 │
        ┌────────▼─────────┐
        │  DBT Transform   │  STG → ODS → DM
        │  (dbt_project/)  │
        └────────┬─────────┘
                 │
                 ▼
        ┌──────────────────┐
        │  Analytics       │  stg.*, ods.*, dm.*
        │  Schemas         │  + Elementary
        └──────────────────┘
```

## Компоненты

### 1. App (FastAPI + MongoDB)
**Директория**: `app/`

Сервис сбора данных через публичные API:
- **Binance Klines API**: OHLCV свечи криптовалют
- **Crypto.news RSS**: Новости о криптовалютах

**Эндпоинты**:
- `GET /api/binance/fetch-klines` - сбор свечей (params: symbol, interval, limit)
- `GET /api/news/fetch-news` - сбор новостей (params: source, limit)
- `GET /health` - проверка подключения к MongoDB

**Технологии**: FastAPI, PyMongo, Pydantic, httpx

### 2. Airflow (Оркестрация)
**Директория**: `airflow/`

Три DAG:
1. **collect_data** (каждый час) - вызывает эндпоинты app для сбора данных
2. **el_process** (каждые 6 часов) - переносит данные MongoDB → PostgreSQL raw
3. **dbt_transformation** (каждые 6 часов) - запускает DBT модели + тесты + Elementary отчёт

**Технологии**: Airflow 2.10.5, LocalExecutor, PostgresHook, dbt-core, elementary-data

### 3. PostgreSQL (DWH)
**Директория**: `dwh/`

**Версия**: PostgreSQL 13

**Схемы**:
- `raw` - сырые JSONB данные из MongoDB
- `stg` - staging (распакованные данные)
- `ods` - operational data store (агрегаты, enrichment)
- `dm` - data marts (аналитические витрины)
- `elementary` - мониторинг качества данных

### 4. DBT (Трансформации)
**Директория**: `dbt_project/`

**Архитектура**: STG → ODS → DM

**Модели**:

#### STG (Staging) - Распаковка JSONB
- `stg_binance_klines` - свечи Binance (symbol, interval, OHLCV, timestamps)
- `stg_news_articles` - новости (title, description, pub_date, categories)
- **Стратегия**: incremental (delete+insert)
- **Особенности**: распаковка JSONB, инкрементальная загрузка

#### ODS (Operational Data Store) - Агрегация
- `ods_binance_daily_agg` - дневные агрегаты (daily OHLC, volume, price_change_pct)
- `ods_news_enriched` - обогащённые новости (sentiment, text metrics)
- **Стратегия**: incremental (delete+insert)
- **Особенности**: CTE, window functions, sentiment analysis

#### DM (Data Marts) - Аналитика
- `dm_crypto_market_overview` - обзор рынка (цены, MA 7d/30d, волатильность, тренды)
- `dm_news_impact_analysis` - корреляция новостей и цен (sentiment vs price changes)
- **Стратегия**: table (full refresh)
- **Особенности**: window functions, CTE, cross joins для корреляций

**SQL техники**:
- Window functions: `avg() over()`, `stddev() over()`, `row_number()`
- CTE (Common Table Expressions) во всех моделях
- JSONB операции: `->>`, `->`, `jsonb_array_length()`
- JOIN для получения first/last значений

**Тестирование**:
- **47 dbt-core тестов** ✅: unique, not_null, accepted_values, relationships
- **10 Elementary тестов** ✅: volume_anomalies, column_anomalies, dimension_anomalies, etc.
- **Итого**: 57 тестов

**Версии** (совместимо с PostgreSQL 13):
- dbt-core==1.8.7
- dbt-postgres==1.8.2
- elementary-data[postgres]==0.16.2

### 5. Elementary (Мониторинг)
**Директория**: `elementary/`

Nginx сервер для раздачи HTML отчётов Elementary с результатами тестов и метриками качества данных.

**URL**: http://localhost:8081/elementary_report.html

## Структура проекта

```
itmo-md-2025/
├── app/                              # FastAPI сервис
│   ├── app/
│   │   ├── main.py                   # Точка входа
│   │   ├── api/                      # Роутеры (binance.py, news.py)
│   │   ├── service/                  # Бизнес-логика
│   │   ├── core/                     # Настройки, логирование
│   │   └── database.py               # MongoDB подключение
│   ├── Dockerfile
│   └── pyproject.toml
├── airflow/                          # Airflow оркестрация
│   ├── dags/
│   │   ├── collect_data_dag.py       # Сбор данных
│   │   ├── el_process_dag.py         # EL MongoDB → PostgreSQL
│   │   ├── dbt_transformation_dag.py # DBT трансформации
│   │   └── utils/                    # Helpers
│   ├── Dockerfile
│   └── requirements.txt              # dbt + elementary
├── dwh/                              # PostgreSQL
│   └── docker-compose.yml
├── dbt_project/                      # DBT проект
│   ├── models/
│   │   ├── sources.yml               # Raw источники
│   │   ├── stg/                      # Staging (2 модели)
│   │   ├── ods/                      # ODS (2 модели)
│   │   └── dm/                       # Data Marts (2 модели)
│   ├── macros/
│   ├── dbt_project.yml
│   ├── profiles.yml                  # Подключение к PostgreSQL
│   ├── packages.yml                  # Elementary
│   └── requirements.txt
├── elementary/                       # Elementary report server
│   └── docker-compose.yml            # Nginx
├── docker-compose.yaml               # Главный compose
├── fix_permissions.sh                # Фикс прав для Airflow
├── DEPLOYMENT.md                     # Инструкции по развёртыванию
└── SUBMISSION.md                     # Данные для сдачи

```

## Быстрый старт

### 1. Клонирование и настройка

```bash
git clone https://github.com/boomb0om/itmo-md-2025.git
cd itmo-md-2025

# Создать .env файлы
cp app/.env.example app/.env
cp dwh/.env.example dwh/.env
cp airflow/.env.example airflow/.env
cp dbt_project/.env.example dbt_project/.env

# Отредактировать при необходимости
nano app/.env
nano dwh/.env
nano airflow/.env
nano dbt_project/.env
```

### 2. Запуск всех сервисов

```bash
# Запуск всего стека
docker-compose up -d

# Проверка статуса
docker ps
```

### 3. Проверка сервисов

- **App Swagger**: http://localhost:8000/docs
- **Airflow UI**: http://localhost:8080 (airflow/airflow)
- **PostgreSQL**: localhost:5433 (analytics/analytics)
- **MongoDB**: localhost:27017 (admin/admin)
- **Elementary Report**: http://localhost:8081/elementary_report.html

### 4. Ручной запуск DAG

1. Откройте Airflow: http://localhost:8080
2. Включите DAG `collect_data`, `el_process`, `dbt_transformation`
3. Запустите их вручную (кнопка ▶)

### 5. Проверка результатов

```sql
-- Подключиться к PostgreSQL
psql -h localhost -p 5433 -U analytics -d analytics

-- Проверить raw данные
SELECT COUNT(*) FROM raw.raw_binance_data;
SELECT COUNT(*) FROM raw.raw_news_data;

-- Проверить STG слой
SELECT COUNT(*) FROM stg.stg_binance_klines;
SELECT COUNT(*) FROM stg.stg_news_articles;

-- Проверить ODS слой
SELECT COUNT(*) FROM ods.ods_binance_daily_agg;
SELECT COUNT(*) FROM ods.ods_news_enriched;

-- Проверить DM витрины
SELECT * FROM dm.dm_crypto_market_overview LIMIT 10;
SELECT * FROM dm.dm_news_impact_analysis LIMIT 10;

-- Проверить Elementary тесты
SELECT * FROM elementary.elementary_test_results
ORDER BY detected_at DESC LIMIT 10;
```

## Разработка

### Локальная разработка App

```bash
cd app
uv sync
uv run uvicorn app.main:app --reload
```

### Локальная работа с DBT

```bash
cd dbt_project

# Установить зависимости
pip install -r requirements.txt

# Загрузить переменные окружения
export $(xargs < .env)

# Установить пакеты Elementary
dbt deps --profiles-dir .

# Проверить подключение
dbt debug --profiles-dir .

# Запустить модели
dbt run --profiles-dir .

# Запустить тесты
dbt test --profiles-dir .

# Сгенерировать Elementary отчёт
edr report --profiles-dir .

# Сгенерировать dbt документацию
dbt docs generate --profiles-dir .
dbt docs serve --port 8001 --profiles-dir .
```

### Pre-commit хуки

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Data Flow

1. **Сбор данных** (каждый час):
   - Airflow DAG `collect_data` → App endpoints → MongoDB

2. **EL процесс** (каждые 6 часов):
   - Airflow DAG `el_process` → MongoDB → PostgreSQL raw (JSONB)

3. **DBT трансформации** (каждые 6 часов):
   - Airflow DAG `dbt_transformation`:
     - `dbt run --select tag:staging` → STG слой
     - `dbt test --select tag:staging`
     - `dbt run --select tag:ods` → ODS слой
     - `dbt test --select tag:ods`
     - `dbt run --select tag:datamart` → DM слой
     - `dbt test` → Все тесты (dbt-core + Elementary)
     - `edr report` → Генерация отчёта

## Требования курса

Проект выполнен в соответствии с требованиями курса ITMO MD 2025:

✅ **Базовый проект (50 баллов)**:
- Python сервис → MongoDB → EL процесс → PostgreSQL raw → DBT (STG → ODS → DM)

✅ **Качество кода (10 баллов)**:
- Pre-commit хуки (ruff, black)
- Документация (README, DEPLOYMENT)
- SQL форматирование, window functions, CTE

✅ **DBT продвинутые возможности (20 баллов)**:
- Jinja шаблоны в каждой модели
- 4 типа dbt-core тестов (47 тестов)
- 6 типов Elementary тестов (10 тестов)
- Документация моделей и колонок
- Теги для управления запуском
- 2 инкрементальные стратегии (delete+insert, table)

**Итого**: 80/120 баллов
**Дополнительно можно**: визуализация (+10), презентация (+10), CI/CD (+10)

Подробнее см. `REQUIREMENTS_CHECKLIST.md`

## Полезные ссылки

- [DBT Documentation](https://docs.getdbt.com/)
- [Elementary Data](https://docs.elementary-data.com/)
- [Airflow Documentation](https://airflow.apache.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Сдача проекта

См. `SUBMISSION.md` для данных по сдаче (URLs, credentials).

См. `DEPLOYMENT.md` для инструкций по развёртыванию на сервере.
