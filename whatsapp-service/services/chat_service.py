import time
from typing import Optional
import os
import requests
import logging
from pymongo import MongoClient
from shared.templates import PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        mongodb_user = os.getenv("MONGODB_USER")
        mongodb_password = os.getenv("MONGODB_PASSWORD")
        mongodb_host = os.getenv("MONGODB_HOST")
        
        mongo_uri = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}?retryWrites=true&w=majority"
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client.whatsapp_db
        self.conversations = self.db.conversations
        self.conversation_history = {}

    async def send_message_to_openai(self, message: str, number: str) -> str:
        try:
            openai_service_url = os.getenv("OPENAI_SERVICE_URL")
            if not openai_service_url:
                raise ValueError("OPENAI_SERVICE_URL not configured")

            response = requests.post(
                f"{openai_service_url}/chat",
                json={"content": message, "user_id": number},
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                logger.error(f"Error from OpenAI service: {response.text}")
                return "Lo siento, hubo un error al procesar tu mensaje."

        except Exception as e:
            logger.error(f"Error in send_message_to_openai: {str(e)}")
            return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

    def log_conversation(
        self,
        user_id: str,
        role: str,
        message: str,
        message_type: str = "text",
        tokens_used: int = 0,
        response_time: float = 0,
        model_version: str = "gpt-4",
        conversation_id: Optional[str] = None,
    ) -> Optional[str]:
        try:
            conversation_doc = {
                "user_id": user_id,
                "role": role,
                "message": message,
                "message_type": message_type,
                "tokens_used": tokens_used,
                "response_time": response_time,
                "model_version": model_version,
                "timestamp": time.time(),
                "conversation_id": conversation_id,
            }
            result = self.conversations.insert_one(conversation_doc)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error registrando en MongoDB: {str(e)}")
            return None

    def get_conversation_history(self, user_id: str, limit: int = 20):
        try:
            return list(
                self.conversations.find(
                    {"user_id": user_id}, {"_id": 0, "message": 1, "role": 1}
                )
                .sort("timestamp", -1)
                .limit(limit)
            )
        except Exception as e:
            logger.error(f"Error obteniendo historial de conversaciones: {str(e)}")
            return []

    def get_or_create_history(self, user_id: str):
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = [
                {"role": "system", "content": PROMPT_TEMPLATE}
            ]
        return self.conversation_history[user_id]
