# Elementary Report Server

Nginx сервер для раздачи Elementary HTML отчётов.

## Запуск

```bash
docker-compose up -d
```

## Доступ

Отчёт доступен по адресу: `http://localhost:8081/elementary_report.html`

## Обновление отчёта

Отчёт генерируется Airflow DAG'ом `dbt_transformation_dag` в задаче `elementary_report`.

Путь к отчёту: `dbt_project/edr_target/elementary_report.html`

## Ручная генерация

```bash
cd ../dbt_project
edr report
# Отчёт будет создан в edr_target/elementary_report.html
```
