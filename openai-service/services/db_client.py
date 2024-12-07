import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from config.database import get_database_settings

logger = logging.getLogger(__name__)

class DBClient:
    def __init__(self):
        self.settings = get_database_settings()
        self.base_url = f"http://{self.settings.DB_SERVICE_HOST}:{self.settings.DB_SERVICE_PORT}"
        self.session = None

    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    async def log_conversation(self, user_id: str, message: str, response: str) -> None:
        """Log conversation to DB service"""
        try:
            await self._ensure_session()
            
            # Log the message and response
            conversation_data = {
                "user_id": user_id,
                "messages": [
                    {"content": message, "sender": user_id},
                    {"content": response, "sender": "assistant"}
                ]
            }
            
            async with self.session.post(
                f"{self.base_url}/conversations/",
                json=conversation_data
            ) as response:
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Error logging conversation: {str(e)}")
            raise

    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history from DB service"""
        try:
            await self._ensure_session()
            async with self.session.get(
                f"{self.base_url}/conversations/{user_id}",
                params={"limit": limit}
            ) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                data = await response.json()
                return data.get("messages", [])
        except Exception as e:
            logger.error(f"Error getting conversation history: {str(e)}")
            raise 