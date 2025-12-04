import json
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional

from utils.db_connections import get_mongo_database


def save_to_mongo(
    collection_name: str,
    data: Dict[str, Any],
    database_name: Optional[str] = None,
) -> str:
    db = get_mongo_database(database_name)
    collection = db[collection_name]
    
    if "created_at" not in data:
        data["created_at"] = datetime.utcnow()
    
    result = collection.insert_one(data)
    return str(result.inserted_id)


def save_batch_to_mongo(
    collection_name: str,
    data_list: List[Dict[str, Any]],
    database_name: Optional[str] = None,
) -> List[str]:
    db = get_mongo_database(database_name)
    collection = db[collection_name]
    
    now = datetime.utcnow()
    for data in data_list:
        if "created_at" not in data:
            data["created_at"] = now
    
    result = collection.insert_many(data_list)
    return [str(id) for id in result.inserted_ids]


def get_data_from_mongo(
    collection_name: str,
    database_name: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict[str, Any]]:
    db = get_mongo_database(database_name)
    collection = db[collection_name]
    
    query = query or {}
    for doc in collection.find(query):
        yield doc


def get_all_data_from_mongo(
    collection_name: str,
    database_name: Optional[str] = None,
    query: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    return list(get_data_from_mongo(collection_name, database_name, query))

