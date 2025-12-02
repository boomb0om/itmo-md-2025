import os
import json
from datetime import datetime
from typing import Dict, Any, List

from dotenv import load_dotenv
from pymongo import MongoClient
from sqlalchemy import create_engine, text, Column, String, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

Base = declarative_base()


def get_mongo_config():
    """Get MongoDB configuration from environment"""
    return {
        "host": os.getenv("MONGO_HOST", "mongodb"),
        "port": int(os.getenv("MONGO_PORT", 27017)),
        "username": os.getenv("MONGO_USERNAME", "admin"),
        "password": os.getenv("MONGO_PASSWORD", "admin"),
        "authSource": os.getenv("MONGO_AUTH_SOURCE", "admin"),
    }


def get_postgres_config():
    """Get PostgreSQL configuration from environment"""
    return {
        "url": f"postgresql://{os.getenv('POSTGRES_USER', 'analytics')}:{os.getenv('POSTGRES_PASSWORD', 'analytics')}@{os.getenv('POSTGRES_HOST', 'postgres-analytics')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'analytics')}"
    }


def get_data_from_mongo(collection_name: str, database_name: str = None):
    """
    Extract data from MongoDB collection
    
    Args:
        collection_name: Name of the MongoDB collection
        database_name: Name of the database (defaults to MONGO_DATABASE env var)
    
    Yields:
        Documents from MongoDB collection
    """
    mongo_config = get_mongo_config()
    client = MongoClient(**mongo_config)
    
    db_name = database_name or os.getenv("MONGO_DATABASE", "crypto_data")
    db = client[db_name]
    collection = db[collection_name]
    
    # Get all documents
    for doc in collection.find():
        yield doc
    
    client.close()


def flatten_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten MongoDB document for PostgreSQL storage
    - Convert _id to string
    - Serialize nested objects to JSONB
    - Convert lists to JSONB
    - Handle datetime objects
    """
    flattened = {}
    
    for key, value in doc.items():
        if key == "_id":
            flattened["mongo_id"] = str(value)
        elif isinstance(value, (dict, list)):
            # Serialize complex types to JSON
            flattened[key] = json.dumps(value, default=str)
        elif isinstance(value, datetime):
            flattened[key] = value
        else:
            flattened[key] = value
    
    return flattened


def create_table_if_not_exists(engine, table_name: str, sample_doc: Dict[str, Any]):
    """
    Create PostgreSQL table if it doesn't exist
    Uses a generic structure with JSONB for complex fields
    """
    with engine.connect() as conn:
        # Create raw schema
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw;"))
        conn.commit()
        
        # Create table with dynamic columns based on sample document
        columns_sql = ["mongo_id VARCHAR PRIMARY KEY"]
        
        for key, value in sample_doc.items():
            if key == "mongo_id":
                continue
            elif isinstance(value, datetime):
                columns_sql.append(f"{key} TIMESTAMP")
            elif isinstance(value, (int, float)):
                columns_sql.append(f"{key} NUMERIC")
            elif isinstance(value, bool):
                columns_sql.append(f"{key} BOOLEAN")
            elif isinstance(value, (dict, list)):
                columns_sql.append(f"{key} JSONB")
            else:
                columns_sql.append(f"{key} TEXT")
        
        # Add created_at and updated_at
        columns_sql.append("created_at TIMESTAMP DEFAULT NOW()")
        columns_sql.append("updated_at TIMESTAMP DEFAULT NOW()")
        
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS raw.{table_name} (
            {', '.join(columns_sql)}
        );
        """
        
        conn.execute(text(create_table_sql))
        conn.commit()


def load_to_postgres(data: List[Dict[str, Any]], table_name: str):
    """
    Load flattened data into PostgreSQL
    
    Args:
        data: List of flattened documents
        table_name: Target table name in raw schema
    """
    postgres_config = get_postgres_config()
    engine = create_engine(postgres_config["url"])
    
    if not data:
        print(f"No data to load for {table_name}")
        return
    
    # Create table if not exists using first document as sample
    sample_doc = flatten_document(data[0])
    create_table_if_not_exists(engine, table_name, sample_doc)
    
    # Prepare data for insertion
    flattened_data = [flatten_document(doc) for doc in data]
    
    # Insert data (simple approach - in production use upsert)
    with engine.connect() as conn:
        for doc in flattened_data:
            # Build INSERT ... ON CONFLICT DO UPDATE
            columns = list(doc.keys())
            values = [doc[col] for col in columns]
            
            placeholders = ", ".join([f":{col}" for col in columns])
            columns_str = ", ".join(columns)
            
            # Add updated_at
            columns_str += ", updated_at"
            placeholders += ", NOW()"
            
            insert_sql = f"""
            INSERT INTO raw.{table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT (mongo_id) DO UPDATE SET
                updated_at = NOW()
            """
            
            conn.execute(text(insert_sql), doc)
        
        conn.commit()
    
    print(f"Loaded {len(flattened_data)} records into raw.{table_name}")


def move_data_to_postgres():
    """
    Main EL function: Extract from MongoDB and Load to PostgreSQL
    Processes klines, news, and requests_log collections
    """
    collections = ["klines", "news", "requests_log"]
    
    for collection_name in collections:
        print(f"Processing collection: {collection_name}")
        
        try:
            # Extract data from MongoDB
            data = list(get_data_from_mongo(collection_name))
            print(f"Extracted {len(data)} documents from {collection_name}")
            
            if data:
                # Load to PostgreSQL
                load_to_postgres(data, collection_name)
            else:
                print(f"No data found in {collection_name}")
        
        except Exception as e:
            print(f"Error processing {collection_name}: {e}")
            raise
    
    print("EL process completed successfully")
    return True

