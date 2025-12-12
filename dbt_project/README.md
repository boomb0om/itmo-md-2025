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
**Стратегия**: `delete+insert` - удаление и вставка по ключам (совместимо с PostgreSQL 13)

**Модели:**
- `ods_binance_daily_agg` - дневная агрегация OHLCV
  - Дневные OHLC, объёмы, количество сделок
  - Изменение цены в процентах
  - CTE с агрегациями + JOIN для расчёта open/close (совместимо с PostgreSQL 13)

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
- **Window Functions**: `avg() over()`, `stddev() over()`, `row_number()` (в DM слое)
- **CTE (Common Table Expressions)**: Все модели ODS и DM используют CTE
- **Aggregations**: `sum()`, `count()`, `max()`, `min()`, `avg()`
- **JSONB операции**: `->>`, `->`, `jsonb_array_length()`
- **JOINs**: LEFT JOIN для получения first/last значений в ODS

### DBT Features
- **Jinja templates**: Макросы `{{ config() }}`, `{{ ref() }}`, `{{ source() }}`, `{% if is_incremental() %}`
- **Incremental models**: Стратегия `delete+insert` (STG и ODS - совместимо с PostgreSQL 13)
- **Tags**: `staging`, `ods`, `datamart` для управления запуском
- **Custom schemas**: Модели создаются в отдельных схемах (stg, ods, dm)
- **Tests**: 4 типа dbt-core тестов (unique, not_null, accepted_values, relationships)
- **Documentation**: Все модели документированы в schema.yml файлах

## Тестирование

### DBT Core Tests (4 типа)
1. **`unique`** - уникальность ID (binance_id, news_id)
2. **`not_null`** - обязательные поля (symbol, open_time, pub_date, etc.)
3. **`accepted_values`** - допустимые значения:
   - interval: ['1m', '5m', '15m', '1h', '4h', '1d']
   - sentiment: ['positive', 'negative', 'neutral']
   - trend_indicator: ['uptrend', 'downtrend', 'sideways']
   - sentiment_price_correlation: ['positive_correlation', 'negative_correlation', 'no_correlation']
4. **`relationships`** - целостность связей:
   - ods_binance_daily_agg.symbol → stg_binance_klines.symbol

**Всего тестов**: 47 (все прошли успешно ✅)

## Настройка и запуск

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
# или
pip install dbt-core==1.8.7 dbt-postgres==1.8.2 elementary-data[postgres]==0.16.2
```

**Важно**: Версии совместимы с PostgreSQL 13 и не имеют конфликтов protobuf.

### 2. Настройка profiles.yml

Создать файл `~/.dbt/profiles.yml`:

```yaml
crypto_analytics:
  target: dev
  outputs:
    dev:
      type: postgres
      host: localhost
      port: 5433
      user: analytics
      password: analytics
      dbname: analytics
      schema: public
      threads: 4
      keepalives_idle: 0
```

Или использовать профиль в папке проекта (файл уже есть в `dbt_project/profiles.yml`).

### 3. Установка пакетов Elementary

```bash
cd dbt_project
dbt deps
```

Это установит пакет `elementary-data/elementary` для мониторинга качества данных.

### 4. Проверка подключения

```bash
dbt debug
```

Должно показать "All checks passed!" ✅

### 5. Запуск моделей

```bash
# Запустить все модели (STG → ODS → DM)
dbt run

# Запустить только конкретный слой
dbt run --select tag:staging
dbt run --select tag:ods
dbt run --select tag:datamart

# Запустить конкретную модель
dbt run --select dm_crypto_market_overview
```

**Результат**: Создаются таблицы в схемах `stg`, `ods`, `dm`.

### 6. Запуск тестов

```bash
# Все тесты (47 штук)
dbt test

# Тесты конкретного слоя
dbt test --select tag:staging

# Тесты конкретной модели
dbt test --select stg_binance_klines
```

**Ожидаемый результат**: `Done. PASS=47 WARN=0 ERROR=0 SKIP=0 TOTAL=47` ✅

### 7. Генерация документации

```bash
# Сгенерировать документацию
dbt docs generate

# Запустить веб-сервер с документацией
dbt docs serve --port 8001
```

Откройте в браузере `http://localhost:8001` для просмотра:
- DAG графа зависимостей моделей
- Описания всех колонок
- Результатов тестов
- SQL кода моделей

### 8. Запуск через Airflow

DAG `dbt_transformation_dag` автоматически запускается каждые 6 часов:

**Последовательность задач:**
1. `dbt_deps` - Установка пакетов
2. `dbt_run_staging` - Запуск STG моделей
3. `dbt_test_staging` - Тесты STG
4. `dbt_run_ods` - Запуск ODS моделей
5. `dbt_test_ods` - Тесты ODS
6. `dbt_run_dm` - Запуск DM моделей
7. `dbt_test_all` - Все тесты
8. `elementary_report` - Генерация отчёта мониторинга

**Airflow UI**: `http://localhost:8080`

## Используемые инкрементальные стратегии

### 1. delete+insert (STG и ODS слои)
```sql
config(
    materialized='incremental',
    incremental_strategy='delete+insert',
    unique_key='binance_id'  # или ['symbol', 'trade_date'] для составного ключа
)
```

**Описание**: Удаляет существующие записи по ключу и вставляет новые.

**Почему используется**:
- Совместимо с PostgreSQL 13 (MERGE появился только в PostgreSQL 15)
- Гарантирует отсутствие дубликатов
- Подходит для данных, которые не изменяются после вставки

**Применяется в**:
- `stg_binance_klines` (unique_key: binance_id)
- `stg_news_articles` (unique_key: news_id)
- `ods_binance_daily_agg` (unique_key: [symbol, trade_date])
- `ods_news_enriched` (unique_key: news_id)

### 2. table (DM слой)
```sql
config(
    materialized='table'
)
```

**Описание**: Полная перезагрузка таблицы при каждом запуске.

**Применяется в**:
- `dm_crypto_market_overview` - агрегирует все данные за весь период
- `dm_news_impact_analysis` - анализ корреляций требует полных данных

## Data Flow

```
MongoDB (binance_data, news_data)
         ↓
    [Airflow EL]
         ↓
PostgreSQL raw.raw_binance_data, raw.raw_news_data (JSONB)
         ↓
    [DBT STG] - delete+insert (инкрементальная загрузка)
         ↓
stg.stg_binance_klines, stg.stg_news_articles
         ↓
    [DBT ODS] - delete+insert (инкрементальная загрузка)
         ↓
ods.ods_binance_daily_agg, ods.ods_news_enriched
         ↓
    [DBT DM] - table (полная перезагрузка)
         ↓
dm.dm_crypto_market_overview, dm.dm_news_impact_analysis
         ↓
    [BI Tools / Analysts / Dashboards]
```

## Полезные команды

```bash
# Документация моделей
dbt docs generate
dbt docs serve --port 8001

# Компиляция SQL без выполнения (для проверки)
dbt compile

# Запуск определённой модели
dbt run --select dm_crypto_market_overview

# Модель и все зависимости (upstream)
dbt run --select +dm_crypto_market_overview

# Модель и все зависящие от неё (downstream)
dbt run --select dm_crypto_market_overview+

# Запуск по тегам
dbt run --select tag:staging
dbt test --select tag:ods

# Полный рефреш (игнорировать инкрементальность)
dbt run --full-refresh

# Очистка артефактов (target/, dbt_packages/)
dbt clean

# Просмотр скомпилированного SQL
cat target/compiled/crypto_analytics/models/dm/dm_crypto_market_overview.sql
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
