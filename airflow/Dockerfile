FROM apache/airflow:2.10.5

USER root

WORKDIR /opt/airflow

COPY requirements.txt .
RUN chown airflow:root requirements.txt && chmod 644 requirements.txt

USER airflow

RUN pip install --no-cache-dir -r requirements.txt
