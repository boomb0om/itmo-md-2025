# Настройка доступа к данным на сервере

## Рекомендуемый подход: Прямое подключение

### Шаг 1: Проверить доступность сервера

```bash
# Проверить доступ к PostgreSQL на сервере
psql -h YOUR_SERVER_IP -p 5432 -U analytics -d analytics -c "SELECT COUNT(*) FROM raw.raw_binance_data;"

# Проверить доступ к MongoDB на сервере
mongosh "mongodb://admin:admin@YOUR_SERVER_IP:27017/crypto_data" --eval "db.binance_data.countDocuments()"
```

Если команды работают - переходи к Шагу 2.
Если не работают - порты закрыты, используй SSH туннель (см. ниже).

---

### Шаг 2: Настроить DBT для работы с сервером

```bash
cd dbt_project

# Создать .env файл
cp .env.example .env
```

Отредактировать `dbt_project/.env`:
```bash
# Заменить на IP или домен твоего сервера
POSTGRES_HOST=YOUR_SERVER_IP
POSTGRES_PORT=5432
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

### Шаг 3: Проверить подключение

```bash
# Загрузить переменные окружения
export $(xargs < .env)

# Установить зависимости
pip install -r requirements.txt

# Проверить подключение dbt
dbt debug --profiles-dir .
```

Должно быть:
```
Connection test: [OK connection ok]
```

### Шаг 4: Запустить DBT

```bash
# Установить пакеты
dbt deps --profiles-dir .

# Запустить модели
dbt run --profiles-dir .

# Проверить что таблицы создались
psql -h YOUR_SERVER_IP -U analytics -d analytics -c "SELECT COUNT(*) FROM stg.stg_binance_klines;"
```

---

## Альтернатива: SSH туннель (если порты закрыты)

### Вариант А: Постоянный туннель в фоне

```bash
# Создать SSH туннель для PostgreSQL (порт 5432 → локальный 5433)
ssh -f -N -L 5433:localhost:5432 user@YOUR_SERVER_IP

# Создать SSH туннель для MongoDB (порт 27017 → локальный 27017)
ssh -f -N -L 27017:localhost:27017 user@YOUR_SERVER_IP

# Проверить что туннели работают
ps aux | grep ssh
```

Теперь в `dbt_project/.env`:
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_USER=analytics
POSTGRES_PASSWORD=analytics
POSTGRES_DB=analytics
```

### Вариант Б: Автоматический туннель в скрипте

Создать файл `start_tunnel.sh`:
```bash
#!/bin/bash

echo "Creating SSH tunnels..."

# PostgreSQL tunnel
ssh -f -N -L 5433:localhost:5432 user@YOUR_SERVER_IP

# MongoDB tunnel (если нужен)
ssh -f -N -L 27017:localhost:27017 user@YOUR_SERVER_IP

echo "Tunnels created!"
echo "PostgreSQL: localhost:5433"
echo "MongoDB: localhost:27017"
```

Запускать перед работой:
```bash
chmod +x start_tunnel.sh
./start_tunnel.sh
```

Остановить туннели:
```bash
# Найти процессы SSH туннелей
ps aux | grep "ssh -f -N -L"

# Убить процессы
kill <PID>
```

---

## Только для тестирования: Экспорт sample данных

Если нужна локальная копия для тестов:

### На сервере: Экспорт sample

```bash
# Подключиться к серверу
ssh user@YOUR_SERVER_IP

# Экспорт первых 1000 записей из PostgreSQL
psql -U analytics -d analytics << 'EOF'
\COPY (SELECT * FROM raw.raw_binance_data ORDER BY process_at DESC LIMIT 1000) TO '/tmp/binance_sample.csv' CSV HEADER
\COPY (SELECT * FROM raw.raw_news_data ORDER BY process_at DESC LIMIT 1000) TO '/tmp/news_sample.csv' CSV HEADER
EOF

echo "Sample data exported to /tmp/"
```

Скачать файлы:
```bash
# Локально
scp user@YOUR_SERVER_IP:/tmp/binance_sample.csv ./
scp user@YOUR_SERVER_IP:/tmp/news_sample.csv ./
```

### Локально: Импорт sample

```bash
# Убедиться что локальный PostgreSQL запущен
docker-compose -f dwh/docker-compose.yml up -d

# Создать схему и таблицы
psql -h localhost -p 5433 -U analytics -d analytics << 'EOF'
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.raw_binance_data (
    id TEXT PRIMARY KEY,
    process_at TIMESTAMP NOT NULL,
    data JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS raw.raw_news_data (
    id TEXT PRIMARY KEY,
    process_at TIMESTAMP NOT NULL,
    data JSONB NOT NULL
);
EOF

# Импортировать CSV
psql -h localhost -p 5433 -U analytics -d analytics << 'EOF'
\COPY raw.raw_binance_data FROM './binance_sample.csv' CSV HEADER
\COPY raw.raw_news_data FROM './news_sample.csv' CSV HEADER
EOF

# Проверить
psql -h localhost -p 5433 -U analytics -d analytics -c "SELECT COUNT(*) FROM raw.raw_binance_data;"
psql -h localhost -p 5433 -U analytics -d analytics -c "SELECT COUNT(*) FROM raw.raw_news_data;"
```

Теперь можно работать локально с `localhost:5433`.

---

## Полный экспорт/импорт (если нужна полная копия)

### На сервере: Полный экспорт PostgreSQL

```bash
# Подключиться к серверу
ssh user@YOUR_SERVER_IP

# Экспорт всей raw схемы (custom формат - быстрее и сжато)
pg_dump -U analytics -d analytics --schema=raw --format=custom -f /tmp/raw_schema.dump

# Или в SQL формате (текстовый, можно посмотреть)
pg_dump -U analytics -d analytics --schema=raw -f /tmp/raw_schema.sql

# Проверить размер
ls -lh /tmp/raw_schema.*
```

Скачать:
```bash
# Локально (custom формат - быстрее)
scp user@YOUR_SERVER_IP:/tmp/raw_schema.dump ./

# Или SQL формат
scp user@YOUR_SERVER_IP:/tmp/raw_schema.sql ./
```

### Локально: Полный импорт PostgreSQL

```bash
# Импорт из custom формата
pg_restore -h localhost -p 5433 -U analytics -d analytics --clean --if-exists ./raw_schema.dump

# Или из SQL формата
psql -h localhost -p 5433 -U analytics -d analytics < ./raw_schema.sql

# Проверить
psql -h localhost -p 5433 -U analytics -d analytics << 'EOF'
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'raw';
EOF
```

### На сервере: Полный экспорт MongoDB

```bash
# Подключиться к серверу
ssh user@YOUR_SERVER_IP

# Экспорт всей базы crypto_data
mongodump \
    --uri="mongodb://admin:admin@localhost:27017" \
    --db=crypto_data \
    --out=/tmp/mongo_dump

# Или только нужные коллекции
mongodump \
    --uri="mongodb://admin:admin@localhost:27017" \
    --db=crypto_data \
    --collection=binance_data \
    --out=/tmp/mongo_dump

mongodump \
    --uri="mongodb://admin:admin@localhost:27017" \
    --db=crypto_data \
    --collection=news_data \
    --out=/tmp/mongo_dump

# Проверить размер
du -sh /tmp/mongo_dump
```

Скачать:
```bash
# Локально
scp -r user@YOUR_SERVER_IP:/tmp/mongo_dump ./
```

### Локально: Полный импорт MongoDB

```bash
# Убедиться что локальный MongoDB запущен
docker-compose -f app/docker-compose.yml up -d mongodb

# Импорт
mongorestore \
    --uri="mongodb://admin:admin@localhost:27017" \
    --drop \
    ./mongo_dump

# Проверить
mongosh "mongodb://admin:admin@localhost:27017/crypto_data" --eval "db.binance_data.countDocuments()"
mongosh "mongodb://admin:admin@localhost:27017/crypto_data" --eval "db.news_data.countDocuments()"
```

---

## Проверка данных после настройки

```bash
# PostgreSQL - проверить количество записей
psql -h YOUR_HOST -p YOUR_PORT -U analytics -d analytics << 'EOF'
SELECT
    'raw_binance' as table_name,
    COUNT(*) as count,
    MIN(process_at) as oldest,
    MAX(process_at) as newest
FROM raw.raw_binance_data
UNION ALL
SELECT
    'raw_news',
    COUNT(*),
    MIN(process_at),
    MAX(process_at)
FROM raw.raw_news_data;
EOF

# Проверить структуру JSONB
psql -h YOUR_HOST -p YOUR_PORT -U analytics -d analytics << 'EOF'
SELECT
    data->>'symbol' as symbol,
    data->>'interval' as interval,
    COUNT(*) as count
FROM raw.raw_binance_data
GROUP BY 1, 2;
EOF
```

---

## Рекомендация

**Для разработки DBT**: Используй **прямое подключение** или **SSH туннель** к серверу. Не нужно копировать данные.

**Для финальной сдачи**: Всё должно работать на сервере, поэтому настрой Airflow и DBT на сервере с прямым подключением к PostgreSQL.

**Для локального теста**: Если хочешь просто проверить что DBT работает - используй **sample данных** (1000 записей).
