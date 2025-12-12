# Развёртывание на сервере

Полная инструкция по развёртыванию проекта на production сервере.

## Требования

- Ubuntu/Debian Linux
- Docker + Docker Compose
- Открытые порты: 8000, 8080, 8081, 5433, 27017
- Минимум 4GB RAM, 20GB disk

## Подготовка сервера

### 1. Установка Docker

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверить
docker --version
docker-compose --version
```

### 2. Открыть порты

```bash
# Для Ubuntu/Debian с ufw
sudo ufw allow 8000/tcp  # App Swagger
sudo ufw allow 8080/tcp  # Airflow
sudo ufw allow 8081/tcp  # Elementary Report
sudo ufw allow 5433/tcp  # PostgreSQL (опционально)
sudo ufw allow 27017/tcp # MongoDB (опционально)

# Проверить статус
sudo ufw status
```

### 3. Клонировать репозиторий

```bash
cd ~
git clone https://github.com/boomb0om/itmo-md-2025.git
cd itmo-md-2025
```

## Настройка окружения

### 1. Создать .env файлы

```bash
# App
cp app/.env.example app/.env
nano app/.env
```

Пример `app/.env`:
```bash
MONGO_URL=mongodb://admin:admin@mongodb:27017/crypto_data?authSource=admin
LOG_LEVEL=INFO
```

```bash
# DWH (PostgreSQL)
cp dwh/.env.example dwh/.env
nano dwh/.env
```

Пример `dwh/.env`:
```bash
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
POSTGRES_PORT=5433
```

```bash
# Airflow
cp airflow/.env.example airflow/.env
nano airflow/.env
```

Пример `airflow/.env`:
```bash
AIRFLOW_UID=$(id -u)
POSTGRES_HOST=postgres-analytics
POSTGRES_PORT=5432
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

```bash
# DBT
cp dbt_project/.env.example dbt_project/.env
nano dbt_project/.env
```

Пример `dbt_project/.env`:
```bash
POSTGRES_HOST=postgres-analytics
POSTGRES_PORT=5432
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

### 2. Исправить права доступа

DBT должен иметь права на запись в директории для логов и артефактов:

```bash
# Автоматический способ
./fix_permissions.sh

# Или вручную
chmod -R 777 dbt_project/logs
chmod -R 777 dbt_project/target
chmod -R 777 dbt_project/edr_target
```

## Запуск проекта

### 1. Запустить все сервисы

```bash
# Запуск всего стека через главный docker-compose
docker-compose up -d

# Проверить что все контейнеры запустились
docker ps
```

Должны быть запущены:
- `app-1` - FastAPI приложение
- `mongodb` - MongoDB
- `airflow-scheduler-1`, `airflow-webserver-1`, `airflow-triggerer-1` - Airflow
- `postgres-analytics` - PostgreSQL DWH
- `elementary-report` - Nginx для Elementary отчётов

### 2. Проверить логи

```bash
# Логи всех сервисов
docker-compose logs

# Логи конкретного сервиса
docker logs app-1
docker logs airflow-scheduler-1
docker logs postgres-analytics
```

### 3. Первый запуск DAG

1. Откройте Airflow UI: `http://<server-ip>:8080`
   - Логин: `airflow`
   - Пароль: `airflow`

2. Включите DAG'и (toggle switch справа):
   - `collect_data` - сбор данных каждый час
   - `el_process` - перенос в PostgreSQL каждые 6 часов
   - `dbt_transformation` - DBT трансформации каждые 6 часов

3. Запустите вручную для проверки (кнопка ▶):
   - Сначала `collect_data` - соберёт данные в MongoDB
   - Затем `el_process` - перенесёт в PostgreSQL raw
   - Затем `dbt_transformation` - создаст STG, ODS, DM таблицы

### 4. Проверить результаты

```bash
# Подключиться к PostgreSQL
docker exec -it postgres-analytics psql -U analytics -d analytics

# В psql:
SELECT COUNT(*) FROM raw.raw_binance_data;
SELECT COUNT(*) FROM raw.raw_news_data;
SELECT COUNT(*) FROM stg.stg_binance_klines;
SELECT COUNT(*) FROM ods.ods_binance_daily_agg;
SELECT * FROM dm.dm_crypto_market_overview LIMIT 10;

# Выйти из psql
\q
```

### 5. Проверить Elementary отчёт

Откройте в браузере: `http://<server-ip>:8081/elementary_report.html`

Если отчёт не сгенерирован, запустите вручную:

```bash
cd ~/itmo-md-2025/dbt_project

# Загрузить переменные окружения
export $(xargs < .env)

# Сгенерировать отчёт
edr report --profiles-dir .

# Проверить что файл создался
ls -la edr_target/elementary_report.html
```

## Обновление кода

### После git pull на сервере

```bash
cd ~/itmo-md-2025

# Получить обновления
git pull

# Исправить права (если были изменения в dbt_project)
./fix_permissions.sh

# Перезапустить сервисы (если были изменения)
docker-compose down
docker-compose up -d

# Если были изменения в Airflow requirements.txt
cd airflow
docker-compose down
docker-compose build
docker-compose up -d
```

## Troubleshooting

### Проблема: Airflow DAG не запускается

**Симптомы**: DAG показывает ошибку "Permission denied" для dbt логов

**Решение**:
```bash
cd ~/itmo-md-2025
./fix_permissions.sh
```

### Проблема: PostgreSQL не доступен

**Проверить**:
```bash
docker ps | grep postgres
docker logs postgres-analytics
```

**Решение**:
```bash
docker-compose restart postgres-analytics
```

### Проблема: DBT не может подключиться к PostgreSQL

**Проверить переменные окружения**:
```bash
cd dbt_project
cat .env
export $(xargs < .env)
dbt debug --profiles-dir .
```

**Если ошибка подключения**:
- Проверить что PostgreSQL запущен: `docker ps | grep postgres`
- Проверить что имя хоста правильное: `postgres-analytics` (для Airflow) или IP сервера (для локального запуска)
- Проверить порт: `5432` внутри Docker сети, `5433` снаружи

### Проблема: Elementary отчёт 403 Forbidden

**Проверить права**:
```bash
ls -la dbt_project/edr_target/
chmod -R 755 dbt_project/edr_target/
```

**Проверить Nginx**:
```bash
docker logs elementary-report
```

### Проблема: MongoDB пустая, нет данных

**Запустить сбор данных вручную**:
1. Открыть Swagger: `http://<server-ip>:8000/docs`
2. Вызвать:
   - `GET /api/binance/fetch-klines?symbol=BTCUSDT&interval=1h&limit=100`
   - `GET /api/news/fetch-news?source=crypto.news&limit=50`

Или через Airflow:
1. Открыть `http://<server-ip>:8080`
2. Запустить DAG `collect_data` вручную (▶)

### Проблема: Не хватает места на диске

**Очистить Docker**:
```bash
# Остановить контейнеры
docker-compose down

# Очистить неиспользуемые образы и volumes
docker system prune -a --volumes

# Запустить заново
docker-compose up -d
```

**Очистить dbt артефакты**:
```bash
cd dbt_project
rm -rf target/ logs/ dbt_packages/
dbt deps --profiles-dir .
```

## Мониторинг

### Проверка статуса сервисов

```bash
# Все контейнеры
docker ps -a

# Использование ресурсов
docker stats

# Логи последние 100 строк
docker-compose logs --tail=100

# Логи в реальном времени
docker-compose logs -f
```

### Проверка размера данных

```bash
# Размер MongoDB
docker exec -it mongodb mongosh --eval "db.stats(1024*1024)"

# Размер PostgreSQL
docker exec -it postgres-analytics psql -U analytics -d analytics -c "
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname IN ('raw', 'stg', 'ods', 'dm')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

### Проверка дисков

```bash
# Использование диска
df -h

# Размер директорий проекта
du -sh ~/itmo-md-2025/*
du -sh ~/itmo-md-2025/airflow/volumes/
```

## Бэкапы

### PostgreSQL бэкап

```bash
# Создать бэкап всех схем
docker exec postgres-analytics pg_dump -U analytics -d analytics -Fc -f /tmp/backup.dump

# Скопировать из контейнера
docker cp postgres-analytics:/tmp/backup.dump ./backup_$(date +%Y%m%d).dump

# Восстановить из бэкапа
docker exec -i postgres-analytics pg_restore -U analytics -d analytics --clean --if-exists < backup_20251213.dump
```

### MongoDB бэкап

```bash
# Создать бэкап
docker exec mongodb mongodump --uri="mongodb://admin:admin@localhost:27017" --out=/tmp/mongo_dump

# Скопировать из контейнера
docker cp mongodb:/tmp/mongo_dump ./mongo_backup_$(date +%Y%m%d)

# Восстановить
docker cp mongo_backup_20251213 mongodb:/tmp/mongo_dump
docker exec mongodb mongorestore --uri="mongodb://admin:admin@localhost:27017" --drop /tmp/mongo_dump
```

## Полезные команды

### Docker

```bash
# Перезапустить все сервисы
docker-compose restart

# Остановить все
docker-compose down

# Остановить и удалить volumes
docker-compose down -v

# Пересобрать образы
docker-compose build --no-cache

# Проверить сеть
docker network ls
docker network inspect itmo-network
```

### DBT

```bash
cd dbt_project
export $(xargs < .env)

# Запустить только staging
dbt run --select tag:staging --profiles-dir .

# Запустить только тесты
dbt test --profiles-dir .

# Полный рефреш (игнорировать инкрементальность)
dbt run --full-refresh --profiles-dir .

# Показать скомпилированный SQL
dbt compile --profiles-dir .
cat target/compiled/crypto_analytics/models/dm/dm_crypto_market_overview.sql
```

### Airflow

```bash
# Перезапустить Airflow
cd airflow
docker-compose restart

# Просмотреть логи конкретного DAG run
docker exec airflow-scheduler-1 airflow dags test dbt_transformation

# Очистить историю DAG
docker exec airflow-scheduler-1 airflow db clean --clean-before-timestamp "2025-01-01"
```

## Финальная проверка

Перед сдачей проекта проверьте что всё работает:

1. ✅ App доступен: `http://<server-ip>:8000/docs`
2. ✅ Airflow доступен: `http://<server-ip>:8080`
3. ✅ Elementary отчёт доступен: `http://<server-ip>:8081/elementary_report.html`
4. ✅ PostgreSQL доступен: `psql -h <server-ip> -p 5433 -U analytics -d analytics`
5. ✅ MongoDB доступен: `mongosh "mongodb://admin:admin@<server-ip>:27017/crypto_data"`
6. ✅ Все DAG'и включены и работают
7. ✅ DBT тесты проходят: 57/57 passed
8. ✅ Данные в таблицах: raw → stg → ods → dm

```bash
# Полная проверка
docker ps  # Все контейнеры UP
docker-compose logs --tail=50  # Нет критических ошибок

# Проверка данных в PostgreSQL
docker exec -it postgres-analytics psql -U analytics -d analytics -c "
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
"
```

Если все проверки прошли - проект готов к сдаче! 🎉

См. `SUBMISSION.md` для URLs и credentials для заполнения Google Forms.
