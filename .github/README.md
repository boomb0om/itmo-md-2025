# CI/CD Configuration

## Workflows

### deploy.yml - Automated Deployment to Server

Triggers on push to `main` branch and performs:

1. **Pull latest code** - Fetches and resets to origin/main
2. **Fix permissions** - Runs `fix_permissions.sh` to set correct ownership (UID 50000) for dbt_project
3. **Restart services** - Stops and rebuilds all Docker containers
4. **Install dbt packages** - Automatically runs `dbt deps` to install Elementary and dbt_utils

#### Required Secrets

Configure these in GitHub repository settings (Settings → Secrets and variables → Actions):

- `SSH_HOST` - Server hostname or IP
- `SSH_USER` - SSH username (must have sudo privileges)
- `SSH_PRIVATE_KEY` - SSH private key for authentication

#### Sudo Configuration

The deployment user must be able to run `fix_permissions.sh` without password prompt:

```bash
# On server, add to /etc/sudoers.d/deploy-user
your-username ALL=(ALL) NOPASSWD: /home/your-username/itmo-md-2025/fix_permissions.sh
```

### app_ci.yml - Application CI

Runs on pull requests to validate code quality.

## Manual Deployment

If you need to deploy manually without CI/CD:

```bash
cd ~/itmo-md-2025
git pull
sudo ./fix_permissions.sh
docker compose down
docker compose up -d --build
sleep 60
docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_project && dbt deps --profiles-dir ."
```

## Automatic Permission Fixing

Permissions are automatically fixed in two ways:

1. **During deployment** - GitHub Actions runs `fix_permissions.sh`
2. **On container startup** - `airflow-init` service sets ownership and permissions

This ensures dbt can write to:
- `dbt_project/dbt_packages/` - Package installation
- `dbt_project/logs/` - dbt logs
- `dbt_project/target/` - Compiled SQL and artifacts
- `dbt_project/*.yml` - Lock files

## Troubleshooting

### Permission denied errors during dbt deps

If you see permission errors despite CI/CD:

```bash
# SSH to server and manually fix
cd ~/itmo-md-2025
sudo ./fix_permissions.sh
docker compose restart airflow-scheduler
```

### Workflow fails on sudo

Ensure the deployment user has passwordless sudo for `fix_permissions.sh`:

```bash
# Check sudo configuration
sudo -l

# Should show:
# NOPASSWD: /home/your-username/itmo-md-2025/fix_permissions.sh
```

### dbt deps timeout in CI/CD

Increase `command_timeout` in deploy.yml if network is slow:

```yaml
command_timeout: 2h  # Default is 1h
```
