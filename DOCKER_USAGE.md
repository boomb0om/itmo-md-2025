# Docker Usage Guide

## Important: Run from Root Directory Only!

**Always run `docker compose` commands from the root directory of the project** (`~/itmo-md-2025`), not from subdirectories.

### Why?

The project uses a **root `docker-compose.yaml`** that includes all services:
- `app/` - Crypto application
- `dwh/` - PostgreSQL analytics database
- `airflow/` - Airflow orchestration
- `elementary/` - Elementary report server

Running from subdirectories creates **separate Docker Compose stacks** with different networks, causing connectivity issues.

### Correct Usage

```bash
# ✅ CORRECT - Run from root
cd ~/itmo-md-2025
docker compose up -d
docker compose ps
docker compose logs -f
docker compose restart airflow-scheduler
```

### Incorrect Usage

```bash
# ❌ WRONG - Don't run from subdirectories
cd ~/itmo-md-2025/airflow
docker compose up -d  # This creates airflow_default network instead of itmo-network!
```

## Initial Setup

1. Ensure all `.env` files exist:
```bash
cd ~/itmo-md-2025
ls -la {app,dwh,airflow,elementary}/.env
```

2. Copy from examples if needed:
```bash
cp app/.env.example app/.env
cp dwh/.env.example dwh/.env
cp airflow/.env.example airflow/.env
cp elementary/.env.example elementary/.env
```

3. Start all services:
```bash
docker compose up -d
```

4. Check status:
```bash
docker compose ps
```

All services should be in `itmo-network` and show as `healthy`.

## Network Architecture

All services communicate via `itmo-network`:
- `mongodb` - MongoDB database
- `postgres-analytics` - PostgreSQL DWH
- `postgres` - Airflow metastore (internal name: `itmo-md-2025-postgres-1`)
- `crypto-app` - Application API
- `airflow-webserver` - Airflow UI
- `airflow-scheduler` - Airflow scheduler
- `elementary-report` - Elementary reports

## Troubleshooting

If you see duplicate containers with different names (e.g., `itmo-md-2025-airflow-scheduler-1` and `airflow-airflow-scheduler-1`):

1. Stop all containers:
```bash
docker compose down
cd airflow && docker compose down && cd ..
```

2. Remove orphan containers:
```bash
docker ps -a | grep airflow | awk '{print $1}' | xargs docker rm -f
```

3. Start from root:
```bash
cd ~/itmo-md-2025
docker compose up -d
```
