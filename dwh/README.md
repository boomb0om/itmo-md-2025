# DWH Module

## Purpose
PostgreSQL data warehouse for storing analytical data extracted from MongoDB.

## Stack
- **Database**: PostgreSQL 13
- **Containerization**: Docker Compose

## Structure
```
dwh/
├── .env                 # Environment variables (create from .env.example)
├── .env.example
└── docker-compose.yml
```

## Start Commands

```bash
cd dwh
cp .env.example .env
# Edit .env if needed
docker-compose up -d
```

## Connection
- **Host**: localhost (external) / postgres-analytics (internal)
- **Port**: 5433 (external) / 5432 (internal)
- **Database**: analytics (default)
- **User**: analytics (default)
- **Password**: analytics (default)

