import logging
from typing import Dict
from config import get_settings
import requests
from loguru import logger


class ChatService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_service_url = self.settings.build_service_url("openai")
        self.db_service_url = self.settings.build_service_url("db")

    async def send_message_to_openai(self, message: str, user_id: str) -> str:
        """Send message to OpenAI service and get response"""
        try:
            logger.info("Sending to OpenAI - User: %s, Message: %s", user_id, message)

            # Format the request payload as expected by OpenAI service
            payload = {
                "content": message,
                "user_id": user_id,
                "message_type": "text",  # Add message type as expected by OpenAI service
            }

            logger.debug(f"Request payload to OpenAI service: {payload}")
            response = requests.post(
                f"{self.openai_service_url}/chat",
                json=payload,
                timeout=30.0,  # Add timeout
            )

            if response.status_code == 200:
                ai_response = response.json()["response"]
                logger.info("OpenAI response received for %s", user_id)
                return ai_response
            else:
                logger.error(f"Error from OpenAI service: {response.text}")
                logger.error(f"Status code: {response.status_code}")
                return "Lo siento, hubo un error al procesar tu mensaje."

        except Exception as e:
            logger.error(f"Error in send_message_to_openai: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

    async def store_message(
        self, user_id: str, message: str, is_user: bool = True
    ) -> None:
        """Store message in DB service"""
        try:
            payload = {
                "user_id": user_id,
                "content": message,
                "sender": user_id if is_user else "assistant",
                "message_type": "text",  # Add consistent message type
            }

            logger.debug(f"Storing message with payload: {payload}")
            response = requests.post(
                f"{self.db_service_url}/api/v1/conversations/messages",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()
            logger.info(f"Message stored successfully for user {user_id}")
        except Exception as e:
            logger.error(f"Error storing message: {str(e)}", exc_info=True)
            raise
