import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
from dotenv import load_dotenv
import certifi
from datetime import datetime
from pymongo.errors import CollectionInvalid


async def init_db():
    """Initialize database with conversations collection and schema validation."""
    try:
        # Load environment variables
        load_dotenv()

        # Get MongoDB credentials
        mongodb_user = os.getenv("MONGODB_USER")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_host = os.getenv("MONGODB_HOST", "tuthoria.qbiwj.mongodb.net")
        db_name = os.getenv("MONGODB_DB_NAME", "chat_db")

        if not all([mongodb_user, mongodb_password, mongodb_host]):
            raise ValueError("Missing MongoDB credentials in environment variables")

        # Construct MongoDB URI
        mongo_uri = (
            f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}"
            "/?retryWrites=true&w=majority"
        )

        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(
            mongo_uri, serverSelectionTimeoutMS=5000, tlsCAFile=certifi.where()
        )

        # Test connection
        await client.admin.command("ping")
        logger.success("Successfully connected to MongoDB")

        # Get database
        db = client[db_name]
        logger.info(f"Using database: {db_name}")

        # Check if collection exists first
        collections = await db.list_collection_names()
        collection_exists = "conversations" in collections

        # Simply create collection without schema if it doesn't exist
        if not collection_exists:
            logger.info("Creating conversations collection...")
            await db.create_collection("conversations")
            logger.info("Collection created successfully")
        else:
            logger.info("Conversations collection already exists")

        # Create or update indexes
        logger.info("Creating/updating indexes...")
        await db.conversations.create_index([("user_id", 1)], unique=True)
        await db.conversations.create_index([("updated_at", -1)])

        # Create test conversation if in development
        if os.getenv("ENVIRONMENT") == "development" and not collection_exists:
            logger.info("Creating test conversation...")
            test_conversation = {
                "user_id": "test_user",
                "messages": [
                    {
                        "content": "Hello",
                        "sender": "test_user",
                        "timestamp": datetime.utcnow(),
                        "message_type": "text",
                    }
                ],
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }
            try:
                await db.conversations.insert_one(test_conversation)
            except Exception as e:
                logger.warning(f"Could not create test conversation: {str(e)}")

        # Close connection
        client.close()
        logger.success("Database initialization completed successfully")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
