FROM apache/airflow:2.7.1

WORKDIR /airflow

COPY requirements.txt .
COPY dags/ /airflow/dags/

RUN pip install --no-cache-dir -r requirements.txt