# Deployment Instructions

## Complete Deployment Guide for Server

Follow these steps **in order** to deploy the project on the server.

### Step 1: Pull Latest Changes

```bash
cd ~/itmo-md-2025
git pull
```

### Step 2: Verify Configuration Files

```bash
# Check that all .env files exist
ls -la {app,dwh,airflow,elementary}/.env

# If elementary/.env is missing, create it:
cp elementary/.env.example elementary/.env

# Verify dbt_project.yml has correct paths (should be "dbt_packages", NOT "/tmp/dbt_packages")
grep "packages-install-path" dbt_project/dbt_project.yml
# Should output: packages-install-path: "dbt_packages"
```

### Step 3: Fix Permissions for dbt Directories

```bash
# Run the permissions fix script
./fix_permissions.sh

# Verify permissions
ls -la dbt_project/ | grep -E "(logs|target|edr|packages)"
# All should show drwxrwxrwx (777)
```

### Step 4: Stop All Services

```bash
# IMPORTANT: Always run docker compose from the ROOT directory
cd ~/itmo-md-2025

# Stop all services
docker compose down

# Remove any orphan containers from subdirectories
docker ps -a | grep -E "airflow|itmo-md" | awk '{print $1}' | xargs -r docker rm -f
```

### Step 5: Clean Old dbt Packages (if needed)

```bash
# If you had permission issues, clean old packages
rm -rf dbt_project/dbt_packages/*
rm -rf dbt_project/logs/*
rm -rf dbt_project/target/*
```

### Step 6: Start All Services

```bash
# Start from ROOT directory
cd ~/itmo-md-2025
docker compose up -d

# Wait for services to become healthy (2-3 minutes)
sleep 120

# Check status - all should be in itmo-network
docker compose ps
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}"
```

### Step 7: Verify dbt Configuration Inside Container

```bash
# Check that container sees correct dbt_project.yml
docker compose exec airflow-scheduler cat /opt/airflow/dbt_project/dbt_project.yml | grep packages-install-path

# Should output: packages-install-path: "dbt_packages"
# NOT: packages-install-path: "/tmp/dbt_packages"
```

### Step 8: Install dbt Packages

```bash
# Install packages from inside the scheduler container
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_project && dbt deps --profiles-dir ."

# Verify packages installed
docker compose exec airflow-scheduler ls -la /opt/airflow/dbt_project/dbt_packages/
# Should see: elementary/ and dbt_utils/
```

### Step 9: Verify DAGs

```bash
# Check Airflow UI
echo "Open http://your-server-ip:8080"
echo "Username: airflow"
echo "Password: airflow"

# Or check DAG list via CLI
docker compose exec airflow-scheduler airflow dags list
```

### Step 10: Test dbt Transformation DAG

```bash
# Trigger the DAG manually to test
docker compose exec airflow-scheduler airflow dags trigger dbt_transformation

# Watch logs in real-time
docker compose logs -f airflow-scheduler
```

## Troubleshooting

### Issue: "No dbt_project.yml found at expected path /tmp/dbt_packages/elementary"

**Cause**: Old version of dbt_project.yml still using /tmp paths

**Fix**:
```bash
cd ~/itmo-md-2025
git pull
docker compose restart airflow-scheduler
```

### Issue: "Permission denied: dbt_packages/dbt_utils"

**Cause**: Wrong file ownership

**Fix**:
```bash
./fix_permissions.sh
docker compose restart airflow-scheduler
```

### Issue: Duplicate containers in different networks

**Cause**: Running docker compose from subdirectories

**Fix**:
```bash
# Stop all
docker compose down
cd airflow && docker compose down && cd ..

# Remove duplicates
docker ps -a | grep airflow | awk '{print $1}' | xargs docker rm -f

# Start from root only
cd ~/itmo-md-2025
docker compose up -d
```

### Issue: Scheduler shows "unhealthy"

**Check logs**:
```bash
docker compose logs airflow-scheduler --tail=100 | grep -i error
```

**Common fixes**:
```bash
# Restart scheduler
docker compose restart airflow-scheduler

# Or full restart
docker compose down && docker compose up -d
```

## Quick Reference

### Always Use Root Directory
```bash
# ✅ CORRECT
cd ~/itmo-md-2025
docker compose [command]

# ❌ WRONG - Don't do this!
cd ~/itmo-md-2025/airflow
docker compose [command]
```

### Check Service Health
```bash
docker compose ps
docker compose logs [service-name]
```

### Useful Commands
```bash
# View all containers and networks
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}"

# Exec into scheduler
docker compose exec airflow-scheduler bash

# View Airflow logs
docker compose logs -f airflow-scheduler

# Restart specific service
docker compose restart airflow-scheduler

# Full restart
docker compose down && docker compose up -d
```

## Architecture

All services run in `itmo-network`:
- `mongodb` (port 27017) - Source data
- `postgres-analytics` (port 5433) - Analytics DWH
- `postgres` (internal) - Airflow metastore
- `redis` (internal) - Airflow queue
- `crypto-app` (port 8000) - Application API
- `airflow-webserver` (port 8080) - Airflow UI
- `airflow-scheduler` - Task orchestration
- `elementary-report` (port 8081) - Data quality reports
