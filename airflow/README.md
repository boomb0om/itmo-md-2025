# Airflow Module

Orchestrates сбор данных и перенос Mongo -> Postgres raw.

## Structure
```
airflow/
├── dags/
│   ├── collect_data_dag.py      # триггерит эндпоинты app каждый час
│   ├── el_process_dag.py        # планировщик EL каждые 6 часов
│   └── utils/                   # подключения и логика переноса
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## DAGs
- `collect_data`: вызывает `/api/binance/fetch-klines` и `/api/news/fetch-news`
- `el_process`: переносит новые документы в `raw.raw_binance_data` и `raw.raw_news_data`

## Run
```
cd airflow
cp .env.example .env
export AIRFLOW_UID=$(id -u)
docker-compose --env-file .env up -d
```

Web UI: http://localhost:8080 (логин/пароль airflow/airflow)
