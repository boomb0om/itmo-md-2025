from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from utils.el_process_logic import move_binance_data_to_postgres, move_news_data_to_postgres

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
    'el_process',
    default_args=default_args,
    description='EL process: Extract from MongoDB and Load to PostgreSQL',
    schedule_interval='0 */6 * * *',
    catchup=False,
    tags=['etl', 'mongo', 'postgres'],
)

task_binance = PythonOperator(
    task_id='move_binance_data_to_postgres',
    python_callable=move_binance_data_to_postgres,
    dag=dag,
)

task_news = PythonOperator(
    task_id='move_news_data_to_postgres',
    python_callable=move_news_data_to_postgres,
    dag=dag,
)

[task_binance, task_news]

