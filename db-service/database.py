from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from config import get_settings
import certifi
from typing import Any


class Database:
    client: Any = None
    settings = get_settings()
    db_name: str = settings.database_name


async def connect_to_database():
    """Connect to MongoDB database."""
    try:
        logger.info("Connecting to MongoDB...")

        Database.client = AsyncIOMotorClient(
            Database.settings.get_mongodb_url(),
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where(),
        )

        # Verify connection
        await Database.client.admin.command("ping")
        logger.success("Successfully connected to MongoDB")

    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise


async def close_database_connection():
    """Close database connection."""
    try:
        if Database.client is not None:
            Database.client.close()
            Database.client = None
            logger.info("Closed MongoDB connection")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")
        raise


async def get_database():
    """Get database instance."""
    if Database.client is None:
        await connect_to_database()
    return Database.client[Database.db_name]
