# Инструкция по развёртыванию DBT проекта

## Предварительные требования

1. Работающий стек:
   - PostgreSQL с raw данными (raw.raw_binance_data, raw.raw_news_data)
   - Airflow контейнер с доступом к PostgreSQL
   - MongoDB с данными (опционально, для локального тестирования EL)

2. Данные в PostgreSQL raw слое должны иметь структуру:
   ```sql
   CREATE TABLE raw.raw_binance_data (
       id TEXT PRIMARY KEY,
       process_at TIMESTAMP NOT NULL,
       data JSONB NOT NULL
   );

   CREATE TABLE raw.raw_news_data (
       id TEXT PRIMARY KEY,
       process_at TIMESTAMP NOT NULL,
       data JSONB NOT NULL
   );
   ```

## Локальное развёртывание

### Шаг 1: Настройка окружения

```bash
cd dbt_project

# Создать .env файл
cp .env.example .env
```

Отредактировать `.env`:
```bash
# Для локального PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics

# Для удалённого сервера
POSTGRES_HOST=your_server_ip
POSTGRES_PORT=5432
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

### Шаг 2: Установка зависимостей

```bash
# Установить dbt и elementary
pip install -r requirements.txt

# Проверить подключение
export $(xargs < .env)
dbt debug --profiles-dir .
```

### Шаг 3: Установка пакетов Elementary

```bash
dbt deps --profiles-dir .
```

Это создаст директорию `dbt_packages/` с пакетом Elementary.

### Шаг 4: Первый запуск моделей

```bash
# Запустить все модели
dbt run --profiles-dir .

# Или по слоям:
dbt run --select tag:staging --profiles-dir .
dbt run --select tag:ods --profiles-dir .
dbt run --select tag:datamart --profiles-dir .
```

### Шаг 5: Запуск тестов

```bash
# Все тесты (включая Elementary)
dbt test --profiles-dir .

# Только dbt-core тесты
dbt test --exclude package:elementary --profiles-dir .

# Только Elementary тесты
dbt test --select package:elementary --profiles-dir .
```

### Шаг 6: Генерация Elementary отчёта

```bash
# Сгенерировать HTML отчёт
edr report --profiles-dir .

# Отчёт будет создан в:
# ./edr_target/elementary_report.html

# Открыть в браузере
open ./edr_target/elementary_report.html  # macOS
xdg-open ./edr_target/elementary_report.html  # Linux
```

## Развёртывание в Airflow

### Шаг 1: Обновить Docker образ Airflow

Файл `airflow/requirements.txt` уже содержит зависимости dbt:
```
dbt-core==1.9.2
dbt-postgres==1.9.0
elementary-data==0.18.2
```

Пересобрать образ:
```bash
cd airflow
docker-compose down
docker-compose build
docker-compose up -d
```

### Шаг 2: Проверить монтирование dbt_project

В `airflow/docker-compose.yml` добавлен volume:
```yaml
volumes:
  - ../dbt_project:/opt/airflow/dbt_project
```

Проверить внутри контейнера:
```bash
docker exec -it airflow-scheduler-1 bash
ls -la /opt/airflow/dbt_project
```

### Шаг 3: Настроить переменные окружения

Убедиться, что в `airflow/.env` или `docker-compose.yml` есть переменные:
```
POSTGRES_HOST=postgres-analytics
POSTGRES_PORT=5432
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

### Шаг 4: Активировать DAG

1. Открыть Airflow UI: http://localhost:8080
2. Найти DAG `dbt_transformation`
3. Включить DAG (toggle switch)
4. Запустить вручную для проверки (кнопка ▶)

### Шаг 5: Проверить выполнение

Проверить логи каждой задачи:
- `dbt_deps` - установка пакетов
- `dbt_run_staging` - запуск STG моделей
- `dbt_test_staging` - тесты STG
- `dbt_run_ods` - запуск ODS моделей
- `dbt_test_ods` - тесты ODS
- `dbt_run_datamart` - запуск DM моделей
- `dbt_test_all` - все тесты
- `elementary_generate_report` - генерация отчёта

## Проверка результатов

### Проверить созданные таблицы в PostgreSQL

```sql
-- STG слой
SELECT * FROM stg.stg_binance_klines LIMIT 10;
SELECT * FROM stg.stg_news_articles LIMIT 10;

-- ODS слой
SELECT * FROM ods.ods_binance_daily_agg LIMIT 10;
SELECT * FROM ods.ods_news_enriched LIMIT 10;

-- DM слой
SELECT * FROM dm.dm_crypto_market_overview;
SELECT * FROM dm.dm_news_impact_analysis LIMIT 20;

-- Elementary мониторинг
SELECT * FROM elementary.elementary_test_results ORDER BY detected_at DESC LIMIT 10;
```

### Проверить количество записей

```sql
SELECT
    'raw_binance' as layer, COUNT(*) as cnt FROM raw.raw_binance_data
UNION ALL
SELECT 'raw_news', COUNT(*) FROM raw.raw_news_data
UNION ALL
SELECT 'stg_binance', COUNT(*) FROM stg.stg_binance_klines
UNION ALL
SELECT 'stg_news', COUNT(*) FROM stg.stg_news_articles
UNION ALL
SELECT 'ods_binance', COUNT(*) FROM ods.ods_binance_daily_agg
UNION ALL
SELECT 'ods_news', COUNT(*) FROM ods.ods_news_enriched
UNION ALL
SELECT 'dm_market', COUNT(*) FROM dm.dm_crypto_market_overview
UNION ALL
SELECT 'dm_news_impact', COUNT(*) FROM dm.dm_news_impact_analysis;
```

## Доступ к Elementary отчёту через веб-сервер

### Вариант 1: Python HTTP сервер (для разработки)

```bash
cd dbt_project/edr_target
python3 -m http.server 8081
# Открыть http://localhost:8081/elementary_report.html
```

### Вариант 2: Nginx (для продакшена)

Создать `docker-compose.yml` для Nginx:
```yaml
version: '3.8'
services:
  elementary-report:
    image: nginx:alpine
    ports:
      - "8081:80"
    volumes:
      - ./dbt_project/edr_target:/usr/share/nginx/html:ro
```

Запустить:
```bash
docker-compose -f docker-compose-nginx.yml up -d
# Открыть http://localhost:8081/elementary_report.html
```

## Troubleshooting

### Проблема: dbt не находит profile

**Ошибка**: `Profile crypto_analytics not found`

**Решение**:
```bash
# Убедиться что .env загружен
export $(xargs < .env)

# Проверить profiles.yml
cat profiles.yml

# Запустить с явным указанием profiles-dir
dbt run --profiles-dir .
```

### Проблема: Не может подключиться к PostgreSQL

**Ошибка**: `could not connect to server`

**Решение**:
```bash
# Проверить доступность PostgreSQL
psql -h localhost -p 5433 -U analytics -d analytics

# Проверить переменные окружения
echo $POSTGRES_HOST
echo $POSTGRES_PORT

# Проверить из Airflow контейнера
docker exec -it airflow-scheduler-1 bash
psql -h postgres-analytics -p 5432 -U analytics -d analytics
```

### Проблема: Raw таблицы пустые

**Решение**:
1. Проверить что EL процесс отработал:
   ```bash
   # Проверить в PostgreSQL
   SELECT COUNT(*) FROM raw.raw_binance_data;
   SELECT COUNT(*) FROM raw.raw_news_data;
   ```

2. Запустить EL DAG вручную в Airflow:
   - Открыть DAG `el_process`
   - Нажать ▶ (Trigger DAG)

3. Проверить логи EL процесса

### Проблема: Elementary тесты не выполняются

**Решение**:
```bash
# Проверить что пакеты установлены
dbt deps --profiles-dir .
ls -la dbt_packages/

# Проверить версию
pip list | grep elementary

# Переустановить elementary
pip install --upgrade elementary-data
```

### Проблема: Инкрементальные модели не обновляются

**Решение**:
```bash
# Полная перезагрузка конкретной модели
dbt run --select stg_binance_klines --full-refresh --profiles-dir .

# Полная перезагрузка всех моделей
dbt run --full-refresh --profiles-dir .
```

## Мониторинг и поддержка

### Регулярные проверки

1. **Ежедневно**: Проверять Elementary отчёт на аномалии
2. **Еженедельно**: Проверять объёмы данных в таблицах
3. **Ежемесячно**: Обновлять зависимости dbt и elementary

### Обновление dbt/Elementary

```bash
# Обновить зависимости
pip install --upgrade dbt-core dbt-postgres elementary-data

# Обновить версии в requirements.txt
pip freeze | grep -E "(dbt-|elementary)" > requirements_new.txt

# Перезапустить Airflow с новыми зависимостями
cd airflow
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Логирование

Все логи dbt в Airflow доступны в UI Airflow:
1. Открыть DAG `dbt_transformation`
2. Выбрать запуск (Run)
3. Кликнуть на задачу
4. Выбрать "Log"

Для локального запуска логи выводятся в консоль.

## Полезные команды

```bash
# Скомпилировать SQL без выполнения
dbt compile --profiles-dir .

# Показать граф зависимостей
dbt docs generate --profiles-dir .
dbt docs serve --profiles-dir .

# Запустить конкретную модель с зависимостями
dbt run --select +dm_crypto_market_overview --profiles-dir .

# Запустить модель и все зависящие от неё
dbt run --select dm_crypto_market_overview+ --profiles-dir .

# Очистить артефакты
dbt clean

# Показать скомпилированный SQL
cat target/compiled/crypto_analytics/models/dm/dm_crypto_market_overview.sql
```
