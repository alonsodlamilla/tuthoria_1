import os
import logging
import requests
from typing import Dict

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.openai_service_url = os.getenv("OPENAI_SERVICE_URL")
        self.db_service_url = os.getenv("DB_SERVICE_URL")
        if not self.openai_service_url:
            raise ValueError("OPENAI_SERVICE_URL not configured")
        if not self.db_service_url:
            raise ValueError("DB_SERVICE_URL not configured")

    async def send_message_to_openai(self, message: str, user_id: str) -> str:
        """Send message to OpenAI service and get response"""
        try:
            response = requests.post(
                f"{self.openai_service_url}/chat",
                json={
                    "content": message,
                    "user_id": user_id
                }
            )

            if response.status_code == 200:
                return response.json()["response"]
            else:
                logger.error(f"Error from OpenAI service: {response.text}")
                return "Lo siento, hubo un error al procesar tu mensaje."

        except Exception as e:
            logger.error(f"Error in send_message_to_openai: {str(e)}")
            return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

    async def store_message(self, user_id: str, message: str, is_user: bool = True) -> None:
        """Store message in DB service"""
        try:
            response = requests.post(
                f"{self.db_service_url}/conversations/messages",
                json={
                    "user_id": user_id,
                    "content": message,
                    "sender": user_id if is_user else "assistant"
                }
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise
