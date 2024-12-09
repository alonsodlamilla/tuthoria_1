from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
from config import get_settings
import certifi
from typing import Any
import asyncio


class Database:
    client: Any = None
    settings = get_settings()
    db_name: str = settings.database_name


async def connect_to_database():
    """Connect to MongoDB database."""
    retry_count = 0
    max_retries = 3

    while retry_count < max_retries:
        try:
            logger.info(
                f"Connecting to MongoDB (attempt {retry_count + 1}/{max_retries})..."
            )
            logger.debug(f"Connection URL: {Database.settings.get_mongodb_url()}")

            Database.client = AsyncIOMotorClient(
                Database.settings.get_mongodb_url(),
                serverSelectionTimeoutMS=5000,
                tlsCAFile=certifi.where(),
            )

            # Verify connection
            await Database.client.admin.command("ping")
            logger.success("Successfully connected to MongoDB")
            return

        except Exception as e:
            retry_count += 1
            logger.error(
                f"Failed to connect to MongoDB (attempt {retry_count}/{max_retries}): {str(e)}"
            )
            if retry_count < max_retries:
                await asyncio.sleep(2**retry_count)  # Exponential backoff
            else:
                logger.critical(
                    "Maximum retry attempts reached. Could not connect to MongoDB"
                )
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
