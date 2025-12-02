from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from typing import Optional
from contextlib import asynccontextmanager

from src.core.settings import mongo_settings
from src.core.logging import logger


client: Optional[MongoClient] = None
db = None


async def connect_mongo():
    """Connect to MongoDB"""
    global client, db
    try:
        client = MongoClient(
            mongo_settings.url,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command('ping')
        db = client[mongo_settings.database]
        await logger.info("Successfully connected to MongoDB")
    except ConnectionFailure as e:
        await logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def disconnect_mongo():
    """Disconnect from MongoDB"""
    global client
    if client:
        client.close()
        await logger.info("MongoDB connection closed")


def get_db():
    """Get MongoDB database instance"""
    if db is None:
        raise RuntimeError("MongoDB not connected")
    return db

