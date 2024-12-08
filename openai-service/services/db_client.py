import httpx
from loguru import logger
from typing import List, Optional

from config.settings import get_settings

class DBClient:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.DB_SERVICE_URL
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get conversation history from DB service"""
        try:
            response = await self.client.get(
                f"{self.base_url}/conversations/{user_id}",
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json().get("messages", [])
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            return []

    async def log_conversation(self, user_id: str, content: str, response: str) -> bool:
        """Log conversation to DB service"""
        try:
            response = await self.client.post(
                f"{self.base_url}/conversations/messages",
                json={
                    "user_id": user_id,
                    "content": content,
                    "response": response
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")
            return False

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()