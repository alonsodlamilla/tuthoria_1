import pytest
from httpx import AsyncClient
from datetime import datetime

@pytest.mark.asyncio
async def test_message_flow():
    """Test the complete message flow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Store incoming message
        message_data = {
            "user_id": "test_user",
            "content": "Hello",
            "sender": "test_user"
        }
        response = await client.post("/api/v1/conversations/messages", json=message_data)
        assert response.status_code == 200

        # 2. Get conversation history
        response = await client.get("/api/v1/conversations/test_user")
        assert response.status_code == 200
        messages = response.json()["messages"]
        assert len(messages) > 0 