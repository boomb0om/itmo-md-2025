# Airflow Module

## Purpose
Apache Airflow orchestration service for scheduling data collection tasks and EL processes (MongoDB to PostgreSQL).

## Stack
- **Orchestrator**: Apache Airflow 2.10.5
- **Executor**: LocalExecutor
- **Database**: PostgreSQL (for Airflow metadata)
- **Containerization**: Docker Compose

## Structure
```
airflow/
├── .env                 # Environment variables (create from .env.example)
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── dags/
    ├── collect_data_dag.py    # Triggers app endpoints every hour
    ├── el_process_dag.py      # EL: MongoDB -> PostgreSQL
    └── el_process_logic.py    # EL logic functions
```

## Start Commands

```bash
cd airflow
cp .env.example .env
# Edit .env if needed (set AIRFLOW__CORE__FERNET_KEY)
export AIRFLOW_UID=$(id -u)
docker-compose up -d
```

## DAGs
- **collect_data**: Runs every hour, triggers `/api/fetch-klines` and `/api/fetch-news`
- **el_process**: Runs every 6 hours, extracts data from MongoDB and loads to PostgreSQL

## Web UI
- **URL**: http://localhost:8080
- **Username**: airflow (default)
- **Password**: airflow (default)
