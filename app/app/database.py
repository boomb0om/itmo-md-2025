from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from app.core.logging import get_logger
from app.core.settings import get_settings

client: MongoClient | None = None
db: Database | None = None


async def connect_mongo():
    """Connect to MongoDB"""
    global client, db
    logger = get_logger(__name__)
    settings = get_settings()
    try:
        client = MongoClient(settings.mongo.url, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        db = client[settings.mongo.database]
        await logger.info("Successfully connected to MongoDB")
    except ConnectionFailure as e:
        await logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def disconnect_mongo():
    """Disconnect from MongoDB"""
    global client
    logger = get_logger(__name__)
    if client:
        client.close()
        await logger.info("MongoDB connection closed")


def get_db() -> Database:
    """Get MongoDB database instance"""
    if db is None:
        raise RuntimeError("MongoDB not connected")
    return db
