#!/bin/bash
# Fix permissions for dbt_project directories accessed by Airflow
# This script must be run with sudo privileges

set -e

echo "Fixing permissions for dbt_project directories..."

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run with sudo"
    echo "Usage: sudo ./fix_permissions.sh"
    exit 1
fi

# Create directories if they don't exist
mkdir -p dbt_project/logs
mkdir -p dbt_project/target
mkdir -p dbt_project/edr_target
mkdir -p dbt_project/dbt_packages

# Change ownership of entire dbt_project to Airflow user (UID 50000)
echo "Setting ownership to Airflow user (50000:0)..."
chown -R 50000:0 dbt_project/

# Make all files and directories writable
echo "Setting write permissions..."
chmod -R a+w dbt_project/

echo ""
echo "✓ Done! Permissions fixed:"
ls -la dbt_project/ | grep -E "(logs|target|edr|packages|\.yml|\.yaml)"

echo ""
echo "Summary:"
echo "- Owner: airflow (UID 50000)"
echo "- All directories: writable by all users"
echo "- Ready for dbt deps and Airflow tasks"
