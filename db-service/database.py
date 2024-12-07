from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger
import os
import ssl
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Database:
    client: AsyncIOMotorClient = None
    db_name: str = "chat_db"

    @classmethod
    def get_database_url(cls) -> str:
        """Get MongoDB connection URL from environment variables."""
        mongodb_user = os.getenv("MONGODB_USER")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_host = os.getenv("MONGODB_HOST")
        
        if not all([mongodb_user, mongodb_password, mongodb_host]):
            raise ValueError("Missing MongoDB credentials in environment variables")
        
        return f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}/{cls.db_name}?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"

async def connect_to_database():
    """Connect to MongoDB database."""
    try:
        logger.info("Connecting to MongoDB...")
        
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        Database.client = AsyncIOMotorClient(
            Database.get_database_url(),
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl=True
        )
        
        # Verify connection
        await Database.client.admin.command('ping')
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
