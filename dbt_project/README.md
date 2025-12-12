# DBT Project - Crypto Analytics

Проект dbt для трансформации данных криптовалютных цен (Binance) и новостей (Crypto.news).

## Структура проекта

```
dbt_project/
├── models/
│   ├── sources.yml              # Определение raw источников данных
│   ├── stg/                     # Staging layer - распаковка JSONB
│   │   ├── stg_binance_klines.sql
│   │   ├── stg_news_articles.sql
│   │   └── stg_schema.yml
│   ├── ods/                     # ODS layer - нормализация и обогащение
│   │   ├── ods_binance_daily_agg.sql
│   │   ├── ods_news_enriched.sql
│   │   └── ods_schema.yml
│   └── dm/                      # Data Mart layer - аналитические витрины
│       ├── dm_crypto_market_overview.sql
│       ├── dm_news_impact_analysis.sql
│       └── dm_schema.yml
├── macros/
│   └── get_custom_schema.sql    # Макрос для управления схемами
├── dbt_project.yml              # Конфигурация проекта
├── profiles.yml                 # Настройки подключения к БД
├── packages.yml                 # Elementary для мониторинга
└── README.md
```

## Архитектура данных

### Слой STG (Staging)
**Стратегия**: `delete+insert` - удаление и вставка данных

**Модели:**
- `stg_binance_klines` - распаковка JSONB свечей Binance (OHLCV)
- `stg_news_articles` - распаковка JSONB новостей

**Описание**: Извлекает данные из raw слоя (JSONB) и преобразует в структурированные таблицы.

### Слой ODS (Operational Data Store)
**Стратегия**: `merge` - слияние данных по ключам

**Модели:**
- `ods_binance_daily_agg` - дневная агрегация OHLCV с использованием оконных функций
  - Дневные OHLC, объёмы, количество сделок
  - Изменение цены в процентах
  - Window functions для расчёта open/close

- `ods_news_enriched` - обогащённые новости
  - Sentiment analysis (positive/negative/neutral)
  - Метрики текста (длина заголовка, описания)
  - Анализ категорий

**Описание**: Нормализует и обогащает данные, добавляет бизнес-логику.

### Слой DM (Data Marts)
**Стратегия**: `table` - полная перезагрузка

**Модели:**
- `dm_crypto_market_overview` - обзор крипторынка
  - Текущие цены
  - Moving averages (7d, 30d) через window functions
  - Волатильность (стандартное отклонение)
  - Индикатор тренда (uptrend/downtrend/sideways)
  - CTE для вычислений

- `dm_news_impact_analysis` - анализ влияния новостей на цены
  - Ежедневные метрики sentiment
  - Соотношение positive/negative новостей
  - Корреляция sentiment и изменения цены
  - Full outer join новостей и цен

**Описание**: Финальные аналитические витрины для дашбордов и отчётов.

## Используемые техники

### SQL Features
- **Window Functions**: `first_value()`, `last_value()`, `avg() over()`, `stddev() over()`
- **CTE (Common Table Expressions)**: Все модели DM используют CTE
- **Aggregations**: `sum()`, `count()`, `max()`, `min()`, `avg()`
- **JSONB операции**: `->>`, `->`, `jsonb_array_length()`

### DBT Features
- **Jinja templates**: Макросы `{{ config() }}`, `{{ ref() }}`, `{{ source() }}`
- **Incremental models**: 2 стратегии - `delete+insert` (STG) и `merge` (ODS)
- **Tags**: `staging`, `ods`, `datamart` для управления запуском
- **Custom schemas**: Модели создаются в отдельных схемах (stg, ods, dm)
- **Tests**: 4 типа dbt-core + 6 типов Elementary

## Тестирование

### DBT Core Tests (4 типа)
1. `unique` - уникальность ID
2. `not_null` - обязательные поля
3. `accepted_values` - допустимые значения (interval, sentiment, trend)
4. `relationships` - целостность связей между таблицами

### Elementary Tests (6 типов)
1. `volume_anomalies` - аномалии в объёме данных
2. `freshness_anomalies` - проверка свежести данных
3. `event_freshness_anomalies` - свежесть событий (pub_date vs process_at)
4. `column_anomalies` - аномалии в значениях колонок (цены, объёмы)
5. `all_columns_anomalies` - проверка всех колонок на аномалии
6. `dimension_anomalies` - распределение категориальных данных (sentiment, source)

## Настройка и запуск

### 1. Установка зависимостей

```bash
pip install dbt-core dbt-postgres elementary-data
```

### 2. Настройка окружения

Создать `.env` файл:
```bash
cp .env.example .env
```

Отредактировать переменные:
```
POSTGRES_HOST=localhost          # или IP сервера
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_PORT=5433
POSTGRES_DB=analytics
```

### 3. Установка пакетов Elementary

```bash
cd dbt_project
dbt deps --profiles-dir .
```

### 4. Запуск моделей

```bash
# Запустить все модели
dbt run --profiles-dir .

# Запустить только STG
dbt run --select tag:staging --profiles-dir .

# Запустить только ODS
dbt run --select tag:ods --profiles-dir .

# Запустить только DM
dbt run --select tag:datamart --profiles-dir .
```

### 5. Запуск тестов

```bash
# Все тесты
dbt test --profiles-dir .

# Тесты конкретного слоя
dbt test --select tag:staging --profiles-dir .
```

### 6. Генерация Elementary отчёта

```bash
# Установить edr CLI
pip install elementary-data[postgres]

# Сгенерировать HTML отчёт
edr report --profiles-dir .

# Отчёт будет сохранён в ./edr_target/elementary_report.html
```

### 7. Запуск через Airflow

DAG `dbt_transformation` автоматически запускается каждые 6 часов:
1. Установка зависимостей (dbt deps)
2. Запуск STG моделей
3. Тестирование STG
4. Запуск ODS моделей
5. Тестирование ODS
6. Запуск DM моделей
7. Запуск всех тестов
8. Генерация Elementary отчёта

## Используемые инкрементальные стратегии

### 1. delete+insert (STG слой)
```sql
config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='binance_id'
)
```
**Описание**: Удаляет существующие записи по ключу и вставляет новые. Подходит для данных, которые не изменяются после вставки.

### 2. merge (ODS слой)
```sql
config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key=['symbol', 'trade_date']
)
```
**Описание**: Использует SQL MERGE для обновления существующих записей и вставки новых. Подходит для данных, которые могут обновляться.

## Data Flow

```
MongoDB (binance_data, news_data)
         ↓
    [Airflow EL]
         ↓
PostgreSQL raw.raw_binance_data, raw.raw_news_data (JSONB)
         ↓
    [DBT STG] - delete+insert
         ↓
stg.stg_binance_klines, stg.stg_news_articles
         ↓
    [DBT ODS] - merge
         ↓
ods.ods_binance_daily_agg, ods.ods_news_enriched
         ↓
    [DBT DM] - table
         ↓
dm.dm_crypto_market_overview, dm.dm_news_impact_analysis
         ↓
    [BI Tools / Analysts]
```

## Полезные команды

```bash
# Документация моделей
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .

# Компиляция SQL без выполнения
dbt compile --profiles-dir .

# Только определённая модель
dbt run --select dm_crypto_market_overview --profiles-dir .

# Модель и все зависимости
dbt run --select +dm_crypto_market_overview --profiles-dir .

# Очистка артефактов
dbt clean
```

## Требования к данным

### Raw слой должен содержать:
- `raw.raw_binance_data` - таблица с колонками (id, process_at, data)
- `raw.raw_news_data` - таблица с колонками (id, process_at, data)

### Формат JSONB:
**Binance data:**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "open_time": "2025-01-01T00:00:00",
  "open": 42000.5,
  "high": 42500.0,
  "low": 41800.0,
  "close": 42300.0,
  "volume": 150.5,
  ...
}
```

**News data:**
```json
{
  "guid": "abc123",
  "source": "crypto.news",
  "title": "Bitcoin surges to new high",
  "link": "https://...",
  "description": "...",
  "pub_date": "2025-01-01T12:00:00",
  "categories": ["bitcoin", "market"]
}
```

## Мониторинг и алерты

Elementary автоматически создаёт схему `elementary` с таблицами:
- `elementary_test_results` - результаты тестов
- `data_monitoring_metrics` - метрики качества данных
- `model_run_results` - результаты запусков моделей

Генерируемый отчёт включает:
- Статус всех тестов
- Графики аномалий
- Линейдж моделей
- Время выполнения

## Контакты и поддержка

При возникновении вопросов обратитесь к преподавателю курса или изучите официальную документацию:
- [DBT Docs](https://docs.getdbt.com/)
- [Elementary Docs](https://docs.elementary-data.com/)
