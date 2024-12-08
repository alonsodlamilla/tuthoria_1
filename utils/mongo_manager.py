from pymongo import MongoClient
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)
load_dotenv()


class MongoManager:
    def __init__(self):
        try:
            mongo_uri = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@mongodb:27017/"
            self.client = MongoClient(mongo_uri)
            self.db = self.client.chatbot
            self.conversations = self.db.conversations
            logger.info("MongoDB connection established")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {str(e)}")
            raise

    def log_conversation(
        self,
        user_id,
        role,
        message,
        message_type="text",
        tokens_used=0,
        response_time=0,
        model_version="gpt-4",
        conversation_id=None,
    ):
        """Log a conversation message to MongoDB"""
        if not conversation_id:
            conversation_id = str(uuid.uuid4())

        document = {
            "conversation_id": conversation_id,
            "timestamp": datetime.now(),
            "user_id": str(user_id),
            "role": role,
            "message": message,
            "message_type": message_type,
            "tokens_used": tokens_used,
            "response_time": response_time,
            "model_version": model_version,
        }

        try:
            self.conversations.insert_one(document)
            logger.info(f"Message logged for user {user_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")
            raise

    def get_conversation_history(self, user_id, limit=20):
        """Retrieve the last messages for a user"""
        try:
            cursor = (
                self.conversations.find(
                    {"user_id": str(user_id)},
                    {"_id": 0},  # Exclude MongoDB _id from results
                )
                .sort("timestamp", 1)
                .limit(limit)
            )

            return list(cursor)
        except Exception as e:
            logger.error(f"Error retrieving history: {str(e)}")
            return []
