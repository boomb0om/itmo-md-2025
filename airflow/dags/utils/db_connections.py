import os
from typing import Optional

import psycopg2
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()


def get_mongo_client() -> MongoClient:
    mongo_config = {
        "host": os.getenv("MONGO_HOST", "mongodb"),
        "port": int(os.getenv("MONGO_PORT", 27017)),
        "username": os.getenv("MONGO_USERNAME", "admin"),
        "password": os.getenv("MONGO_PASSWORD", "admin"),
        "authSource": os.getenv("MONGO_AUTH_SOURCE", "admin"),
    }
    
    return MongoClient(**mongo_config)


def get_mongo_database(database_name: Optional[str] = None):
    client = get_mongo_client()
    db_name = database_name or os.getenv("MONGO_DATABASE", "crypto_data")
    return client[db_name]


def get_postgres_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres-analytics"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        user=os.getenv("POSTGRES_USER", "analytics"),
        password=os.getenv("POSTGRES_PASSWORD", "analytics"),
        database=os.getenv("POSTGRES_DB", "analytics"),
    )

