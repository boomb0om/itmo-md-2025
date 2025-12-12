# DWH Module

PostgreSQL 13 для raw-слоя, куда Airflow пишет `raw_binance_data` и `raw_news_data`.

## Structure
```
dwh/
├── docker-compose.yml
├── .env.example
└── .env
```

## Run
```
cd dwh
cp .env.example .env
docker-compose --env-file .env up -d
```

## Connection
- Host: localhost (контейнер: postgres-analytics)
- Port: 5433 внешний / 5432 внутренний
- Database: analytics
- User/Password: analytics
