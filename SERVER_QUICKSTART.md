# Быстрый старт на сервере

## После git pull

Выполните эти команды на сервере после обновления кода:

```bash
cd ~/itmo-md-2025

# 1. Исправить права доступа для Airflow
./fix_permissions.sh

# 2. Перезапустить Airflow (если были изменения в requirements)
cd airflow
docker-compose down
docker-compose build
docker-compose up -d

# 3. Проверить что все контейнеры работают
cd ..
docker ps

# 4. Проверить доступность сервисов
echo "Swagger: http://213.171.30.141:8000/docs"
echo "Airflow: http://213.171.30.141:8080"
echo "Elementary: http://213.171.30.141:8081/elementary_report.html"
```

## Если Airflow DAG не работает

```bash
# Проверить логи
docker logs airflow-scheduler-1

# Перезапустить DAG вручную в UI
# http://213.171.30.141:8080

# Или из командной строки
docker exec airflow-scheduler-1 airflow dags test dbt_transformation
```

## Обновление Elementary отчёта

```bash
cd ~/itmo-md-2025/dbt_project

# Загрузить переменные окружения
export $(xargs < .env)

# Сгенерировать отчёт
edr report --profiles-dir .

# Проверить
ls -la edr_target/elementary_report.html
```

Отчёт автоматически будет доступен по адресу:
http://213.171.30.141:8081/elementary_report.html
