from typing import Optional, Tuple, Dict
import os
from dotenv import load_dotenv
import logging
from pymongo import MongoClient
from datetime import datetime
from config.database import get_database_settings

logger = logging.getLogger(__name__)


class DBService:
    def __init__(self):
        # Get database settings
        self.settings = get_database_settings()

        # Initialize MongoDB connection
        self.mongo_client = MongoClient(
            self.settings.mongodb_uri, serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        self.mongo_db = self.mongo_client[self.settings.MONGO_DB_NAME]
        self.conversations = self.mongo_db.conversations
        self.user_states = self.mongo_db.user_states

        # Verify connection
        self._verify_connection()

    def _verify_connection(self):
        """Verify MongoDB connection"""
        try:
            # The ismaster command is cheap and does not require auth
            self.mongo_client.admin.command("ismaster")
            logger.info(
                f"Successfully connected to MongoDB ({self.settings.ENVIRONMENT})"
            )
        except Exception as e:
            logger.error(f"MongoDB connection failed: {str(e)}")
            raise

    async def get_user_state(self, user_id: str) -> Tuple[str, Dict[str, str]]:
        """Get user state and context from MongoDB"""
        try:
            state_doc = self.user_states.find_one({"user_id": user_id})

            if not state_doc:
                new_state = {
                    "user_id": user_id,
                    "current_state": "INICIO",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                }
                self.user_states.insert_one(new_state)
                return "INICIO", {}

            return state_doc["current_state"], {
                "anio": state_doc.get("anio"),
                "curso": state_doc.get("curso"),
                "seccion": state_doc.get("seccion"),
            }
        except Exception as e:
            logger.error(f"Error in get_user_state: {str(e)}")
            raise

    async def update_user_state(
        self, user_id: str, state: str, context: Dict[str, str]
    ) -> None:
        """Update user state and context in MongoDB"""
        try:
            update_data = {
                "current_state": state,
                "updated_at": datetime.utcnow(),
                **context,
            }

            self.user_states.update_one(
                {"user_id": user_id}, {"$set": update_data}, upsert=True
            )
        except Exception as e:
            logger.error(f"Error in update_user_state: {str(e)}")
            raise

    async def log_conversation(self, user_id: str, message: str, response: str) -> None:
        """Log conversation to MongoDB"""
        try:
            conversation_doc = {
                "user_id": user_id,
                "message": message,
                "response": response,
                "created_at": datetime.utcnow(),
                "model": "gpt-4",  # You might want to make this configurable
                "metadata": {
                    "source": "openai_service",
                    "type": "chat",
                },
            }

            self.conversations.insert_one(conversation_doc)
        except Exception as e:
            logger.error(f"Error in log_conversation: {str(e)}")
            raise

    async def get_conversation_history(
        self, user_id: str, limit: int = 10
    ) -> list[Dict]:
        """Get conversation history from MongoDB"""
        try:
            return list(
                self.conversations.find(
                    {"user_id": user_id},
                    {"_id": 0, "message": 1, "response": 1, "created_at": 1},
                )
                .sort("created_at", -1)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error in get_conversation_history: {str(e)}")
            raise
