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

    async def get_user_state(self, user_id: str) -> Tuple[str, Dict[str, str]]:
        """Get user state and context from DB service"""
        try:
            await self._ensure_session()
            async with self.session.get(f"{self.base_url}/conversations/{user_id}/state") as response:
                if response.status == 404:
                    return "INICIO", {}
                response.raise_for_status()
                data = await response.json()
                return data["current_state"], {
                    "anio": data.get("anio"),
                    "curso": data.get("curso"),
                    "seccion": data.get("seccion"),
                }
        except Exception as e:
            logger.error(f"Error in get_user_state: {str(e)}")
            raise

    async def update_user_state(self, user_id: str, state: str, context: Dict[str, str]) -> None:
        """Update user state and context via DB service"""
        try:
            await self._ensure_session()
            update_data = {
                "current_state": state,
                "updated_at": datetime.utcnow().isoformat(),
                **context
            }
            async with self.session.put(
                f"{self.base_url}/conversations/{user_id}/state",
                json=update_data
            ) as response:
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Error in update_user_state: {str(e)}")
            raise

    async def log_conversation(self, user_id: str, message: str, response: str) -> None:
        """Log conversation via DB service"""
        try:
            await self._ensure_session()
            conversation_data = {
                "content": message,
                "sender": user_id
            }
            # First, ensure conversation exists
            async with self.session.post(
                f"{self.base_url}/conversations/",
                json={"title": f"Chat with {user_id}", "participants": [user_id]}
            ) as response:
                if response.status not in [200, 409]:  # 409 means conversation already exists
                    response.raise_for_status()
                
            # Add the message
            async with self.session.post(
                f"{self.base_url}/conversations/{user_id}/messages",
                json=conversation_data
            ) as response:
                response.raise_for_status()

            # Add the response
            response_data = {
                "content": response,
                "sender": "assistant"
            }
            async with self.session.post(
                f"{self.base_url}/conversations/{user_id}/messages",
                json=response_data
            ) as response:
                response.raise_for_status()
        except Exception as e:
            logger.error(f"Error in log_conversation: {str(e)}")
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
                return [
                    {
                        "message": msg["content"] if msg["sender"] == user_id else None,
                        "response": msg["content"] if msg["sender"] == "assistant" else None,
                        "created_at": msg["timestamp"]
                    }
                    for msg in data.get("messages", [])[-limit:]
                ]
        except Exception as e:
            logger.error(f"Error in get_conversation_history: {str(e)}")
            raise 