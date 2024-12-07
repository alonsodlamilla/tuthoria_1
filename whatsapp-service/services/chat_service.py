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
        self.openai_service_url = os.getenv("OPENAI_SERVICE_URL")
        self.db_service_url = os.getenv("DB_SERVICE_URL")

    async def send_message_to_openai(self, message: str, number: str) -> str:
        try:
            # Send directly to OpenAI service, let it handle state
            response = requests.post(
                f"{self.openai_service_url}/chat",
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

    # Remove MongoDB-specific methods as they should be in DB service
