from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from bson import ObjectId
from psycopg2.extras import Json

from utils.db_connections import get_postgres_connection, get_mongo_database
from utils.postgres_utils import create_raw_table_if_not_exists


def convert_mongo_doc_to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    result = {}
    for key, value in doc.items():
        if key == "_id":
            result["_id"] = str(value)
        elif hasattr(value, 'isoformat'):
            result[key] = value.isoformat()
        else:
            result[key] = value
    
    return result


def get_processed_ids(conn, table_name: str) -> Set[str]:
    with conn.cursor() as cursor:
        cursor.execute(f"SELECT id FROM raw.{table_name}")
        return {row[0] for row in cursor.fetchall()}


def save_batch_to_raw_layer(
    data_list: List[Dict[str, Any]],
    table_name: str = "raw_data",
    conn=None,
) -> List[str]:
    if conn is None:
        conn = get_postgres_connection()
        should_close = True
    else:
        should_close = False
    
    try:
        process_at = datetime.now(timezone.utc)
        doc_ids = []
        
        with conn.cursor() as cursor:
            for data in data_list:
                doc_id = data.get("_id")
                if not doc_id:
                    continue
                
                doc_ids.append(doc_id)
                
                insert_sql = f"""
                INSERT INTO raw.{table_name} (id, process_at, data)
                VALUES (%s, %s, %s::jsonb)
                ON CONFLICT (id) DO UPDATE SET
                    process_at = EXCLUDED.process_at,
                    data = EXCLUDED.data
                """
                
                cursor.execute(
                    insert_sql,
                    (doc_id, process_at, Json(data))
                )
            
            conn.commit()
        
        return doc_ids
    finally:
        if should_close:
            conn.close()


def move_binance_data_to_postgres():
    collection_name = "binance_data"
    table_name = "raw_binance_data"
    
    conn = get_postgres_connection()
    
    try:
        print(f"Processing collection: {collection_name}")
        create_raw_table_if_not_exists(conn, table_name)

        processed_ids = get_processed_ids(conn, table_name)
        print(f"Found {len(processed_ids)} already processed documents")
        
        db = get_mongo_database()
        collection = db[collection_name]
        
        query = {}
        if processed_ids:
            object_ids = [ObjectId(id) for id in processed_ids if ObjectId.is_valid(id)]
            if object_ids:
                query = {"_id": {"$nin": object_ids}}
        
        mongo_docs = list(collection.find(query))
        print(f"Extracted {len(mongo_docs)} new documents from {collection_name}")
        
        if not mongo_docs:
            print(f"No new data found in {collection_name}")
            return True
        
        data_list = [convert_mongo_doc_to_dict(doc) for doc in mongo_docs]
        
        doc_ids = save_batch_to_raw_layer(
            data_list,
            table_name=table_name,
            conn=conn
        )
        
        print(f"Loaded {len(doc_ids)} records into raw.{table_name}")
        
    except Exception as e:
        print(f"Error processing {collection_name}: {e}")
        raise
    finally:
        conn.close()
    
    return True


def move_news_data_to_postgres():
    collection_name = "news_data"
    table_name = "raw_news_data"
    
    conn = get_postgres_connection()
    
    try:
        print(f"Processing collection: {collection_name}")
        create_raw_table_if_not_exists(conn, table_name)

        processed_ids = get_processed_ids(conn, table_name)
        print(f"Found {len(processed_ids)} already processed documents")
        
        db = get_mongo_database()
        collection = db[collection_name]
        
        query = {}
        if processed_ids:
            object_ids = [ObjectId(id) for id in processed_ids if ObjectId.is_valid(id)]
            if object_ids:
                query = {"_id": {"$nin": object_ids}}
        
        mongo_docs = list(collection.find(query))
        print(f"Extracted {len(mongo_docs)} new documents from {collection_name}")
        
        if not mongo_docs:
            print(f"No new data found in {collection_name}")
            return True
        
        data_list = [convert_mongo_doc_to_dict(doc) for doc in mongo_docs]
        
        doc_ids = save_batch_to_raw_layer(
            data_list,
            table_name=table_name,
            conn=conn
        )
        
        print(f"Loaded {len(doc_ids)} records into raw.{table_name}")
        
    except Exception as e:
        print(f"Error processing {collection_name}: {e}")
        raise
    finally:
        conn.close()
    
    return True

