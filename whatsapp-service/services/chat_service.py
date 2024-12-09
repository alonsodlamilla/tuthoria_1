import logging
from typing import Dict
from config import get_settings
import requests

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_service_url = self.settings.build_service_url("openai")
        self.db_service_url = self.settings.build_service_url("db")

    async def send_message_to_openai(self, message: str, user_id: str) -> str:
        """Send message to OpenAI service and get response"""
        try:
            logger.info("Sending to OpenAI - User: %s, Message: %s", user_id, message)
            response = requests.post(
                f"{self.openai_service_url}/chat",
                json={"content": message, "user_id": user_id},
            )

            if response.status_code == 200:
                ai_response = response.json()["response"]
                logger.info("OpenAI response received for %s", user_id)
                return ai_response
            else:
                logger.error(f"Error from OpenAI service: {response.text}")
                return "Lo siento, hubo un error al procesar tu mensaje."

        except Exception as e:
            logger.error(f"Error in send_message_to_openai: {str(e)}")
            return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

    async def store_message(
        self, user_id: str, message: str, is_user: bool = True
    ) -> None:
        """Store message in DB service"""
        try:
            response = requests.post(
                f"{self.db_service_url}/conversations/messages",
                json={
                    "user_id": user_id,
                    "content": message,
                    "sender": user_id if is_user else "assistant",
                },
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}")
            raise
