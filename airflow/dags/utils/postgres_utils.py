from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from psycopg2.extras import Json

from utils.db_connections import get_postgres_connection


def create_raw_schema_if_not_exists(conn=None):
    if conn is None:
        conn = get_postgres_connection()
        should_close = True
    else:
        should_close = False
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            conn.commit()
    finally:
        if should_close:
            conn.close()


def create_raw_table_if_not_exists(conn=None, table_name: str = "raw_data"):
    if conn is None:
        conn = get_postgres_connection()
        should_close = True
    else:
        should_close = False
    
    try:
        create_raw_schema_if_not_exists(conn)
        
        with conn.cursor() as cursor:
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS raw.{table_name} (
                id VARCHAR PRIMARY KEY,
                process_at TIMESTAMP NOT NULL DEFAULT NOW(),
                data JSONB NOT NULL
            );
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
    finally:
        if should_close:
            conn.close()
