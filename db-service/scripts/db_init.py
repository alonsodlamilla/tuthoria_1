import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
from dotenv import load_dotenv
import certifi

async def init_db():
    """Initialize database and create necessary collections and indexes."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get MongoDB credentials
        mongodb_user = os.getenv("MONGODB_USER")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_host = os.getenv("MONGODB_HOST", "tuthoria.qbiwj.mongodb.net")
        db_name = "chat_db"
        
        if not all([mongodb_user, mongodb_password, mongodb_host]):
            raise ValueError("Missing MongoDB credentials in environment variables")
        
        # Construct MongoDB URI with connection options
        mongo_uri = (
            f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}"
            "/?retryWrites=true&w=majority"
        )
        
        # Connect to MongoDB with proper TLS config
        logger.info("Connecting to MongoDB...")
        client = AsyncIOMotorClient(
            mongo_uri,
            serverSelectionTimeoutMS=5000,
            tlsCAFile=certifi.where()
        )
        
        # Test connection
        await client.admin.command('ping')
        logger.success("Successfully connected to MongoDB")
        
        # Get database
        db = client[db_name]
        logger.info(f"Using database: {db.name}")
        
        # List existing collections
        collections = await db.list_collection_names()
        logger.info(f"Existing collections: {collections}")
        
        # Create collections if they don't exist
        if 'conversations' not in collections:
            logger.info("Creating conversations collection...")
            await db.create_collection('conversations')
            
            # Create indexes
            logger.info("Creating indexes for conversations collection...")
            await db.conversations.create_index([("user_id", 1)])
            await db.conversations.create_index([("created_at", -1)])
            
        if 'user_states' not in collections:
            logger.info("Creating user_states collection...")
            await db.create_collection('user_states')
            
            # Create indexes
            logger.info("Creating indexes for user_states collection...")
            await db.user_states.create_index([("user_id", 1)], unique=True)
        
        # Verify collections
        collections = await db.list_collection_names()
        logger.success(f"Final collections: {collections}")
        
        # Close connection
        client.close()
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(init_db()) 