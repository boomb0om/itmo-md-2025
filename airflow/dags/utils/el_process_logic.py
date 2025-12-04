from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import uuid4

from psycopg2.extras import Json

from utils.db_connections import get_postgres_connection
from utils.mongo_utils import get_all_data_from_mongo
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
        create_raw_table_if_not_exists(conn, table_name)

        process_at = datetime.now(timezone.utc)
        doc_ids = []
        
        with conn.cursor() as cursor:
            for data in data_list:
                doc_id = data.get("_id", str(uuid4()))
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


def move_data_to_postgres():
    """
    Extract data from requests_log collection in MongoDB and load to PostgreSQL.
    The app saves all requests/responses to requests_log, so we process only this collection.
    """
    collection_name = "requests_log"
    
    conn = get_postgres_connection()
    
    try:
        print(f"Processing collection: {collection_name}")
        
        mongo_docs = get_all_data_from_mongo(collection_name)
        print(f"Extracted {len(mongo_docs)} documents from {collection_name}")
        
        if not mongo_docs:
            print(f"No data found in {collection_name}")
            return True
        
        data_list = [convert_mongo_doc_to_dict(doc) for doc in mongo_docs]
        
        table_name = "raw_requests_log"
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
    
    print("EL process completed successfully")
    return True

