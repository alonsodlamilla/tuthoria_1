from typing import Optional, Tuple, Dict
import os
from dotenv import load_dotenv
import logging
import psycopg2
from psycopg2.extras import DictCursor
from pymongo import MongoClient
from datetime import datetime

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class DBService:
    def __init__(self):
        # PostgreSQL config
        self.pg_config = {
            "host": os.getenv("DB_HOST", "postgres"),
            "database": os.getenv("DB_NAME", "docente_bot"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "secret"),
        }

        # MongoDB config
        mongo_uri = f"mongodb://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}@{os.getenv('MONGO_HOST')}:{os.getenv('MONGO_PORT')}/"
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client.openai_service
        self.conversations = self.mongo_db.conversations
        self.user_states = self.mongo_db.user_states

    def _validate_config(self):
        """Validate required environment variables"""
        required_vars = {
            "PostgreSQL": ["DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD"],
            "MongoDB": ["MONGO_HOST", "MONGO_PORT", "MONGO_USER", "MONGO_PASSWORD"],
        }

        for service, vars in required_vars.items():
            missing = [var for var in vars if not os.getenv(var)]
            if missing:
                logger.warning(
                    f"Missing {service} environment variables: {', '.join(missing)}"
                )

    def get_pg_connection(self):
        """Get PostgreSQL connection"""
        try:
            return psycopg2.connect(**self.pg_config)
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
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
