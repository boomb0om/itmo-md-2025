"""
DBT Transformation DAG
Runs dbt models to transform raw data into analytics-ready datasets.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'dbt_transformation',
    default_args=default_args,
    description='Run dbt transformations: STG -> ODS -> DM layers',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['dbt', 'transformation', 'analytics'],
)

# Set environment variables and dbt project path
dbt_project_dir = '/opt/airflow/dbt_project'
dbt_profiles_dir = '/opt/airflow/dbt_project'

# Environment variables for PostgreSQL connection
env_vars = {
    'POSTGRES_HOST': 'postgres-analytics',
    'POSTGRES_PORT': '5432',
    'POSTGRES_USER': 'analytics',
    'POSTGRES_PASSWORD': 'analytics',
    'POSTGRES_DB': 'analytics',
}

# Task 1: Install dbt dependencies (Elementary, etc.)
dbt_deps = BashOperator(
    task_id='dbt_deps',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt deps --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 2: Run dbt models with staging tag
dbt_run_stg = BashOperator(
    task_id='dbt_run_staging',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt run --select tag:staging --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 3: Test staging models
dbt_test_stg = BashOperator(
    task_id='dbt_test_staging',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt test --select tag:staging --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 4: Run dbt models with ods tag
dbt_run_ods = BashOperator(
    task_id='dbt_run_ods',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt run --select tag:ods --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 5: Test ODS models
dbt_test_ods = BashOperator(
    task_id='dbt_test_ods',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt test --select tag:ods --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 6: Run dbt models with datamart tag
dbt_run_dm = BashOperator(
    task_id='dbt_run_datamart',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt run --select tag:datamart --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 7: Test all models (including DM)
dbt_test_all = BashOperator(
    task_id='dbt_test_all',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/dbt test --profiles-dir {dbt_profiles_dir}',
    env=env_vars,
    dag=dag,
)

# Task 8: Generate Elementary report (OPTIONAL - won't fail DAG if OOM)
# Aggressive memory optimization for 4GB RAM server:
# - PYTHONMALLOC='malloc': reduce Python memory overhead
# - days-back 1: process only last day of data
# - exclude-elementary-models: exclude Elementary's internal models from report
# - || true: don't fail DAG if Elementary crashes (OOM, etc.)
# - retries=0: don't retry on failure to save resources
elementary_env = env_vars.copy()
elementary_env['PYTHONMALLOC'] = 'malloc'

elementary_report = BashOperator(
    task_id='elementary_generate_report',
    bash_command=f'cd {dbt_project_dir} && /home/airflow/.local/bin/edr report --profiles-dir {dbt_profiles_dir} --days-back 1 --exclude-elementary-models || true',
    env=elementary_env,
    dag=dag,
    retries=0,
)

# Define task dependencies
dbt_deps >> dbt_run_stg >> dbt_test_stg >> dbt_run_ods >> dbt_test_ods >> dbt_run_dm >> dbt_test_all >> elementary_report
