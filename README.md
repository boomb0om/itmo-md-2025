# ITMO MD 2025 - Crypto Data Pipeline

Проект по курсу "Управление данными" в ИТМО

Отчет по дз-1: [https://github.com/boomb0om/itmo-md-2025/blob/main/docs/hw1.md](https://github.com/boomb0om/itmo-md-2025/blob/main/docs/hw1.md)

## Описание проекта

Система сбора и обработки данных о криптовалютах для анализа влияния новостей на волатильность рынка.

**Кейс:** Влияние новостей на криптовалюты  
**Бизнес-задача:** Помочь трейдерам принимать решения на основе новостей

### Источники данных
- Цены криптовалют (Binance API)
- Новости из RSS-лент (CryptoPanic)

### Ключевые задачи
- Корреляция новостей и волатильности
- Анализ тональности текстов

## Архитектура

Проект состоит из трех модулей:

### 1. `app/` - Data Collection Service
FastAPI приложение для сбора данных:
- **Endpoints:**
  - `GET /api/fetch-klines` - получение данных свечей с Binance
  - `GET /api/fetch-news` - получение новостей из CryptoPanic
- **Хранилище:** MongoDB
- **Stack:** FastAPI, uv, pydantic-settings, aiologger

### 2. `dwh/` - Data Warehouse
PostgreSQL база данных для аналитических данных:
- **Назначение:** Хранение данных после EL процесса
- **Stack:** PostgreSQL 13

### 3. `airflow/` - Orchestration Service
Apache Airflow для оркестрации процессов:
- **DAGs:**
  - `collect_data` - сбор данных каждый час
  - `el_process` - перенос данных из MongoDB в PostgreSQL каждые 6 часов
- **Stack:** Apache Airflow 2.10.5

## Быстрый старт

### Предварительные требования
- Docker и Docker Compose
- Python 3.11+ (для локальной разработки)

### Установка

1. **Клонируйте репозиторий:**
```bash
git clone <repository-url>
cd itmo-md-2025
```

2. **Создайте .env файлы для каждого модуля:**
```bash
# App module
cp app/.env.example app/.env

# DWH module
cp dwh/.env.example dwh/.env

# Airflow module
cp airflow/.env.example airflow/.env
```

3. **Настройте Airflow (сгенерируйте Fernet key):**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Добавьте полученный ключ в `airflow/.env` как `AIRFLOW__CORE__FERNET_KEY=...`

4. **Запустите все сервисы:**
```bash
docker-compose up -d
```

### Проверка работы

1. **App Service:**
   - Health check: http://localhost:8000/health
   - API docs: http://localhost:8000/docs

2. **Airflow WebUI:**
   - URL: http://localhost:8080
   - Username: `airflow`
   - Password: `airflow`

3. **PostgreSQL DWH:**
   - Host: `localhost`
   - Port: `5433`
   - Database: `analytics`
   - User: `analytics`
   - Password: `analytics`

4. **MongoDB:**
   - Host: `localhost`
   - Port: `27017`
   - Database: `crypto_data`

## Структура проекта

```
itmo-md-2025/
├── app/                    # FastAPI приложение
│   ├── src/
│   │   ├── core/          # Настройки и логирование
│   │   └── services/      # Сервисы для работы с API
│   ├── main.py
│   ├── docker-compose.yml
│   └── README.md
├── dwh/                    # Data Warehouse
│   ├── docker-compose.yml
│   └── README.md
├── airflow/                # Airflow оркестрация
│   ├── dags/              # DAG определения
│   ├── docker-compose.yml
│   └── README.md
├── context/                # Описание заданий
├── course/                 # Примеры из курса
└── docker-compose.yaml     # Root compose файл
```

## Модули

### App Module
См. [app/README.md](app/README.md)

**Запуск:**
```bash
cd app
docker-compose up -d
```

### DWH Module
См. [dwh/README.md](dwh/README.md)

**Запуск:**
```bash
cd dwh
docker-compose up -d
```

### Airflow Module
См. [airflow/README.md](airflow/README.md)

**Запуск:**
```bash
cd airflow
export AIRFLOW_UID=$(id -u)
docker-compose up -d
```

## EL Процесс

EL (Extract-Load) процесс реализован в Airflow DAG `el_process`:
- **Извлечение:** Данные из MongoDB (коллекции: klines, news, requests_log)
- **Трансформация:** Упрощение структуры, сериализация JSON полей
- **Загрузка:** Данные в PostgreSQL в схему `raw`

Процесс запускается автоматически каждые 6 часов.

## Разработка

### Локальная разработка App

```bash
cd app
cp .env.example .env
uv pip install -e .
uvicorn main:app --reload
```

### Просмотр логов

```bash
# App logs
docker-compose logs -f app

# Airflow logs
docker-compose logs -f airflow-scheduler
docker-compose logs -f airflow-webserver

# DWH logs
docker-compose logs -f postgres-analytics
```

## Остановка сервисов

```bash
docker-compose down
```

Для полной очистки (включая volumes):
```bash
docker-compose down -v
```

## Дополнительная информация

- **Дедлайн:** 2025-12-06
- **Курс:** Управление данными, ИТМО
- **Примеры:** См. `course/dbt-practice/` для референсной реализации
