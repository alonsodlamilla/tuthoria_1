import httpx
from loguru import logger
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from datetime import datetime

from config.settings import get_settings


class DBClient:
    def __init__(self):
        logger.info("Initializing DBClient")
        self.settings = get_settings()
        self.base_url = self.settings.DB_SERVICE_URL
        logger.debug(f"Using DB service URL: {self.base_url}")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_conversation_history(
        self, user_id: str, limit: int = 10
    ) -> List[dict]:
        """Get conversation history from DB service"""
        logger.info(f"Getting conversation history for user {user_id}")
        logger.debug(f"History limit: {limit}")

        try:
            url = f"{self.base_url}/conversations/{user_id}"
            logger.debug(f"Making GET request to: {url}")

            response = await self.client.get(url, params={"limit": limit})
            response.raise_for_status()

            data = response.json()
            messages = data.get("messages", [])
            logger.info(f"Retrieved {len(messages)} messages for user {user_id}")
            logger.debug(f"Response status code: {response.status_code}")

            return messages

        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}", exc_info=True)
            logger.error(f"User ID: {user_id}")
            logger.error(f"URL attempted: {self.base_url}/conversations/{user_id}")
            return []

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def store_message(
        self, user_id: str, content: str, is_user: bool = True
    ) -> bool:
        """Store message with retries"""
        logger.info(f"Storing message for user {user_id}")
        logger.debug(f"Message type: {'user' if is_user else 'assistant'}")

        try:
            url = f"{self.base_url}/conversations/messages"
            payload = {
                "user_id": user_id,
                "content": content,
                "sender": user_id if is_user else "assistant",
                "message_type": "text",
                "timestamp": datetime.utcnow().isoformat(),
            }
            logger.debug(f"Making POST request to: {url}")
            logger.debug(f"Request payload: {payload}")

            response = await self.client.post(
                url,
                json=payload,
                timeout=10.0,
            )
            response.raise_for_status()

            logger.info(f"Successfully stored message for user {user_id}")
            logger.debug(f"Response status code: {response.status_code}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to store message after retries: {str(e)}", exc_info=True
            )
            logger.error(f"User ID: {user_id}")
            logger.error(f"Content length: {len(content)}")
            logger.error(f"Is user message: {is_user}")
            return False

    async def close(self):
        """Close the HTTP client"""
        logger.info("Closing DB client")
        await self.client.aclose()
