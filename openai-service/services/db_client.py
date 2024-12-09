import httpx
from loguru import logger
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import get_settings


class DBClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.DB_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_conversation_history(
        self, user_id: str, limit: int = 10
    ) -> List[dict]:
        """Get conversation history from DB service"""
        try:
            response = await self.client.get(
                f"{self.base_url}/conversations/{user_id}", params={"limit": limit}
            )
            response.raise_for_status()
            return response.json().get("messages", [])
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def store_message(
        self, user_id: str, content: str, is_user: bool = True
    ) -> bool:
        """Store message with retries"""
        try:
            response = await self.client.post(
                f"{self.base_url}/conversations/messages",
                json={
                    "user_id": user_id,
                    "content": content,
                    "sender": user_id if is_user else "assistant",
                },
                timeout=10.0,
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Failed to store message after retries: {str(e)}")
            return False  # Continue flow even if DB storage fails

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
