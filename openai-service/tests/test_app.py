import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app import app


@pytest.fixture
def test_client():
    return TestClient(app)


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()


@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test chat endpoint"""
    with patch("services.chat_service.ChatService") as MockChatService, patch(
        "services.db_client.DBClient"
    ) as MockDBClient:
        # Mock chat service
        mock_chat_service = MockChatService.return_value
        mock_chat_service.process_message = AsyncMock(return_value="Test response")

        # Mock DB client
        mock_db_client = MockDBClient.return_value
        mock_db_client.get_conversation_history = AsyncMock(return_value=[])

        with TestClient(app) as client:
            response = client.post(
                "/chat", json={"content": "test message", "user_id": "test_user"}
            )

            assert response.status_code == 200
            assert response.json()["response"] == "Test response"

            # Verify conversation history was fetched
            mock_db_client.get_conversation_history.assert_called_once()
            # Verify message was processed
            mock_chat_service.process_message.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation():
    """Test conversation history endpoint"""
    with patch("services.db_client.DBClient") as MockDBClient:
        mock_client = MockDBClient.return_value
        mock_client.get_conversation_history = AsyncMock(
            return_value=[{"message": "test"}]
        )

        with TestClient(app) as client:
            response = client.get("/conversations/test_user")
            assert response.status_code == 200
            assert "messages" in response.json()
