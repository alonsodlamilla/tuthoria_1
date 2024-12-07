from motor.motor_asyncio import AsyncIOMotorClient
from .config import get_settings

settings = get_settings()


class Database:
    client: AsyncIOMotorClient = None


async def get_database() -> AsyncIOMotorClient:
    return Database.client[settings.database_name]


async def connect_to_database():
    Database.client = AsyncIOMotorClient(settings.get_mongodb_url())


async def close_database_connection():
    if Database.client is not None:
        Database.client.close()
