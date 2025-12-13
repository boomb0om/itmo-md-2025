#!/bin/bash
# Fix permissions for dbt_project directories accessed by Airflow

echo "Fixing permissions for dbt_project directories..."

# Create directories if they don't exist
mkdir -p dbt_project/logs
mkdir -p dbt_project/target
mkdir -p dbt_project/edr_target
mkdir -p dbt_project/dbt_packages

# Make them writable by all (needed for Docker containers)
chmod -R 777 dbt_project/logs
chmod -R 777 dbt_project/target
chmod -R 777 dbt_project/edr_target
chmod -R 777 dbt_project/dbt_packages

echo "Done! Permissions fixed:"
ls -la dbt_project/ | grep -E "(logs|target|edr|packages)"
