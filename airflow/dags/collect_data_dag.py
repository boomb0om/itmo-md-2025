from datetime import datetime, timedelta
import os
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

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
    'collect_data',
    default_args=default_args,
    description='Trigger app endpoints to collect cryptocurrency data (app saves to requests_log in MongoDB)',
    schedule_interval='0 * * * *', # every hour
    catchup=False,
    tags=['data_collection', 'crypto'],
)


def trigger_klines_collection():
    """Trigger app endpoint to fetch klines. App will save data to requests_log in MongoDB."""
    app_host = os.getenv("APP_HOST", "crypto-app")
    app_port = os.getenv("APP_PORT", "8000")
    url = f"http://{app_host}:{app_port}/api/fetch-klines"
    
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "limit": 100
    }
    
    print(f"Triggering {url} with params: {params}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    print(f"Klines collection triggered successfully. Status: {result}")
    
    return result


def trigger_news_collection():
    """Trigger app endpoint to fetch news. App will save data to requests_log in MongoDB."""
    app_host = os.getenv("APP_HOST", "crypto-app")
    app_port = os.getenv("APP_PORT", "8000")
    url = f"http://{app_host}:{app_port}/api/fetch-news"
    
    params = {
        "source": "cryptopanic",
        "limit": 50
    }
    
    print(f"Triggering {url} with params: {params}")
    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    item_count = len(result.get('rss', {}).get('channel', {}).get('item', []))
    print(f"News collection triggered successfully. Fetched {item_count} news items")
    
    return result


task_klines = PythonOperator(
    task_id='trigger_klines_collection',
    python_callable=trigger_klines_collection,
    dag=dag,
)

task_news = PythonOperator(
    task_id='trigger_news_collection',
    python_callable=trigger_news_collection,
    dag=dag,
)

[task_klines, task_news]

