# Шаблон для сдачи проекта

Заполните данные для сдачи проекта в Google Sheets.

## Формат сдачи

```
Swagger URL: http://<server-ip>:8000/docs
MongoDB URL: mongodb://root:root@<server-ip>:27017/crypto_data
PostgreSQL URL: postgresql://analytics:analytics@<server-ip>:5433/analytics
Airflow:
   URL: http://<server-ip>:8080
   User: airflow
   Password: airflow
Elementary edr report URL: http://<server-ip>:8081/elementary_report.html
Презентация URL: <ссылка-на-презентацию>
```

## Как получить данные

### Swagger URL
```bash
echo "http://$(hostname -I | awk '{print $1}'):8000/docs"
```

### MongoDB URL
Из файла `app/.env`:
- MONGO_INITDB_ROOT_USERNAME
- MONGO_INITDB_ROOT_PASSWORD
- MONGO_INITDB_DATABASE

Формат: `mongodb://<username>:<password>@<server-ip>:27017/<database>`

### PostgreSQL URL
Из файла `dwh/.env`:
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

Формат: `postgresql://<username>:<password>@<server-ip>:5433/<database>`

### Airflow
- URL: `http://<server-ip>:8080`
- По умолчанию User/Password: `airflow/airflow`

### Elementary Report
- URL: `http://<server-ip>:8081/elementary_report.html`

## Проверка доступности

```bash
# Проверить все порты
netstat -tuln | grep -E ':(8000|8080|8081|5433|27017)'

# Или через lsof
lsof -i :8000
lsof -i :8080
lsof -i :8081
lsof -i :5433
lsof -i :27017
```

## Открытие портов (если необходимо)

```bash
# Для Ubuntu/Debian с ufw
sudo ufw allow 8000/tcp  # App Swagger
sudo ufw allow 8080/tcp  # Airflow
sudo ufw allow 8081/tcp  # Elementary Report
sudo ufw allow 5433/tcp  # PostgreSQL
sudo ufw allow 27017/tcp # MongoDB

# Проверить статус
sudo ufw status
```
