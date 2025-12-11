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
        await init_indexes()
    except ConnectionFailure as e:
        await logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def init_indexes():
    """Initialize MongoDB indexes"""
    logger = get_logger(__name__)
    try:
        db = get_db()

        # Create unique index on guid field for news_data
        news_collection = db.get_collection("news_data")
        news_collection.create_index("guid", unique=True)
        await logger.info("Created index on 'guid' field in 'news_data' collection")
    except Exception as e:
        if "index already exists" in str(e).lower():
            await logger.info("Index already exists, skipping creation")
        else:
            await logger.warning(f"Failed to create indexes for news_data: {e}")

    try:
        db = get_db()
        # Create unique compound index on (interval, open_time) for binance_data
        binance_collection = db.get_collection("binance_data")
        binance_collection.create_index([("interval", 1), ("open_time", 1)], unique=True)
        await logger.info(
            "Created compound index on ('interval', 'open_time') fields in "
            "'binance_data' collection"
        )
    except Exception as e:
        if "index already exists" in str(e).lower():
            await logger.info("Index already exists, skipping creation")
        else:
            await logger.warning(f"Failed to create indexes for binance_data: {e}")


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
