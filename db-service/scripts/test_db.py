import asyncio
from loguru import logger
import sys
import os
from datetime import datetime

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import connect_to_database, close_database_connection, get_database
from models.conversation import ConversationCreate, MessageCreate

async def test_database_operations():
    """Test basic database operations."""
    try:
        logger.info("Starting database operations test...")
        
        # Connect to database
        await connect_to_database()
        db = await get_database()
        
        # Test creating a conversation
        logger.info("Testing conversation creation...")
        conversation = ConversationCreate(
            title="Test Conversation",
            participants=["test_user"]
        )
        
        conv_dict = conversation.dict()
        conv_dict["messages"] = []
        conv_dict["created_at"] = datetime.utcnow()
        conv_dict["updated_at"] = datetime.utcnow()
        
        result = await db.conversations.insert_one(conv_dict)
        logger.success(f"Created conversation with ID: {result.inserted_id}")
        
        # Test adding a message
        logger.info("Testing message addition...")
        message = MessageCreate(
            content="Test message",
            sender="test_user"
        )
        
        message_dict = message.dict()
        message_dict["timestamp"] = datetime.utcnow()
        
        update_result = await db.conversations.update_one(
            {"_id": result.inserted_id},
            {
                "$push": {"messages": message_dict},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        logger.success(f"Added message to conversation: {update_result.modified_count} document modified")
        
        # Test retrieving conversation
        logger.info("Testing conversation retrieval...")
        conversation = await db.conversations.find_one({"_id": result.inserted_id})
        logger.success(f"Retrieved conversation: {conversation}")
        
        # Test deleting conversation
        logger.info("Testing conversation deletion...")
        delete_result = await db.conversations.delete_one({"_id": result.inserted_id})
        logger.success(f"Deleted conversation: {delete_result.deleted_count} document deleted")
        
        # Close connection
        await close_database_connection()
        logger.success("Database operations test completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database operations test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(test_database_operations()) 