# Quick Start Guide - Zero to Running in 5 Minutes

## Prerequisites
- Git repository cloned
- Docker and Docker Compose installed
- Sudo access for permissions script

## Step-by-Step Deployment

### 1. Pull Latest Code
```bash
cd ~/itmo-md-2025
git checkout fix/dbt-dag-and-credentials  # or main after merge
git pull
```

### 2. Verify Configuration
```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

If verification fails, fix the reported issues before continuing.

### 3. Create Environment Files (if missing)
```bash
# Check which .env files are missing
ls -la {app,dwh,airflow,elementary}/.env

# Copy from examples if needed
[ ! -f app/.env ] && cp app/.env.example app/.env
[ ! -f dwh/.env ] && cp dwh/.env.example dwh/.env
[ ! -f airflow/.env ] && cp airflow/.env.example airflow/.env
[ ! -f elementary/.env ] && cp elementary/.env.example elementary/.env
```

### 4. Fix Permissions
```bash
sudo ./fix_permissions.sh
```

Expected output:
```
✓ Done! Permissions fixed:
- Owner: airflow (UID 50000)
- All directories: writable by all users
```

### 5. Create Docker Network (if doesn't exist)
```bash
docker network create itmo-network 2>/dev/null || true
```

### 6. Start All Services
```bash
# Stop any existing containers from subdirectories
docker compose down 2>/dev/null
cd airflow && docker compose down 2>/dev/null && cd ..

# Start from ROOT directory only
cd ~/itmo-md-2025
docker compose up -d
```

### 7. Wait for Services to Initialize
```bash
echo "Waiting for services to become healthy..."
sleep 120

# Check status
docker compose ps
```

All services should show "healthy" status.

### 8. Verify Everything Works

```bash
# Check all containers are in itmo-network
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Networks}}" | grep itmo

# Check Airflow scheduler is healthy
docker compose ps airflow-scheduler

# Check dbt packages installed
docker compose exec airflow-scheduler ls -la /opt/airflow/dbt_project/dbt_packages/
# Should see: elementary/ and dbt_utils/
```

### 9. Access Web Interfaces

- **Airflow UI**: http://your-server:8080
  - Username: `airflow`
  - Password: `airflow`

- **Elementary Reports**: http://your-server:8081

- **Application API**: http://your-server:8000
  - Docs: http://your-server:8000/docs

### 10. Trigger First DAG Run

Option A - Via UI:
1. Open Airflow UI
2. Enable `dbt_transformation` DAG (toggle switch)
3. Click "Trigger DAG" button

Option B - Via CLI:
```bash
docker compose exec airflow-scheduler airflow dags trigger dbt_transformation
```

## Monitoring the Run

### Watch Logs in Real-Time
```bash
# All scheduler logs
docker compose logs -f airflow-scheduler

# Only dbt-related logs
docker compose logs -f airflow-scheduler | grep dbt

# Only errors
docker compose logs -f airflow-scheduler | grep ERROR
```

### Check DAG Status
```bash
docker compose exec airflow-scheduler airflow dags list-runs -d dbt_transformation --state running
```

## Expected Results

### Successful Run Shows:
- ✅ `dbt_deps`: SUCCESS (installs Elementary + dbt_utils)
- ✅ `dbt_run_staging`: SUCCESS (2 staging models)
- ✅ `dbt_test_staging`: SUCCESS (28 tests, warnings OK)
- ✅ `dbt_run_ods`: SUCCESS (2 ODS models)
- ✅ `dbt_test_ods`: SUCCESS
- ✅ `dbt_run_datamart`: SUCCESS (2 datamart models)
- ✅ `dbt_test_all`: SUCCESS (all tests)
- ✅ `elementary_generate_report`: SUCCESS

### Expected Warnings (Normal):
- Elementary anomaly detection warnings (severity: warn)
- Deprecated functionality warnings (will be addressed in future updates)

## Troubleshooting

### Services Not Starting?
```bash
# Check logs
docker compose logs postgres-analytics
docker compose logs airflow-scheduler

# Common fix: recreate everything
docker compose down -v
docker compose up -d
```

### Permission Denied Errors?
```bash
sudo ./fix_permissions.sh
docker compose restart airflow-scheduler
```

### dbt deps Fails?
```bash
# Check configuration
./verify_setup.sh

# Manually run deps
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_project && dbt deps --profiles-dir ."
```

### DAG Not Appearing?
```bash
# Check DAG files
docker compose exec airflow-scheduler ls -la /opt/airflow/dags/

# Refresh DAGs
docker compose restart airflow-scheduler
```

### Network Issues?
```bash
# Verify all containers in same network
docker network inspect itmo-network | grep Name

# Recreate network
docker network rm itmo-network
docker network create itmo-network
docker compose up -d
```

## Maintenance Commands

### View All Running Services
```bash
docker compose ps
```

### Restart Specific Service
```bash
docker compose restart airflow-scheduler
docker compose restart airflow-webserver
```

### View Service Logs
```bash
docker compose logs -f [service-name]
```

### Clean Restart
```bash
docker compose down
sudo ./fix_permissions.sh
docker compose up -d
```

### Update After Git Pull
```bash
git pull
sudo ./fix_permissions.sh
docker compose down
docker compose up -d --build
sleep 60
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_project && dbt deps --profiles-dir ."
```

## Success Indicators

✅ All containers show `healthy` status
✅ Airflow UI accessible on port 8080
✅ `dbt_transformation` DAG visible and enabled
✅ First run completes successfully (may have warnings)
✅ Elementary report generates
✅ No ERROR messages in logs (warnings are OK)

## Next Steps

After successful deployment:
1. Review Elementary data quality reports at http://your-server:8081
2. Check collected data in `collect_data` DAG
3. Monitor EL process in `el_process` DAG
4. Set up regular monitoring via Airflow email alerts (optional)

## Support

If issues persist:
1. Run `./verify_setup.sh` and fix reported issues
2. Check DEPLOYMENT.md for detailed instructions
3. Review DOCKER_USAGE.md for Docker best practices
4. Check `.github/README.md` for CI/CD configuration
