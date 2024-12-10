import logging
from typing import Dict, Optional
from config import get_settings
import httpx
from loguru import logger
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential


class ChatService:
    def __init__(self):
        self.settings = get_settings()
        self.openai_service_url = self.settings.build_service_url("openai")
        self.db_service_url = self.settings.build_service_url("db")
        self.client = httpx.AsyncClient(timeout=60.0)

    async def send_message_to_openai(self, message: str, user_id: str) -> str:
        """Send message to OpenAI service and get response"""
        try:
            logger.info("Sending to OpenAI - User: %s, Message: %s", user_id, message)

            payload = {
                "content": message,
                "user_id": user_id,
                "message_type": "text",
            }

            logger.debug(f"Request payload to OpenAI service: {payload}")
            response = await self.client.post(
                f"{self.openai_service_url}/chat",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            ai_response = data["response"]
            logger.info("OpenAI response received for %s", user_id)
            return ai_response

        except httpx.TimeoutException:
            logger.error("Timeout while waiting for OpenAI response")
            return "Lo siento, el servicio está tardando demasiado. Por favor, intenta nuevamente."
        except Exception as e:
            logger.error(f"Error in send_message_to_openai: {str(e)}", exc_info=True)
            return "Lo siento, hubo un error. ¿Podemos intentar nuevamente?"

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def store_message(
        self,
        user_id: str,
        content: str,
        sender: str,
        message_type: str = "text",
        timestamp: Optional[datetime] = None,
    ) -> bool:
        """Store message in DB service with retries"""
        try:
            payload = {
                "user_id": user_id,
                "content": content,
                "sender": sender,
                "message_type": message_type,
                "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            }

            logger.debug(f"Storing message with payload: {payload}")
            response = await self.client.post(
                f"{self.db_service_url}/api/v1/conversations/messages",
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

            logger.info(f"Message stored successfully for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error storing message: {str(e)}", exc_info=True)
            logger.error(f"Failed payload: {payload}")
            raise

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
