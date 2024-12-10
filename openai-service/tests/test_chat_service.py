import pytest
from httpx import AsyncClient
from datetime import datetime
from unittest.mock import AsyncMock, patch
from services.chat_service import ChatService
from models.chat import Message, ChatResponse, ConversationMessage
from fastapi.testclient import TestClient
from app import app


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def mock_db_client():
    with patch("services.db_client.DBClient") as mock:
        client = mock.return_value
        client.get_conversation_history = AsyncMock(return_value=[])
        client.store_message = AsyncMock(return_value=True)
        yield client


@pytest.fixture
def mock_chat_service():
    with patch("services.chat_service.ChatService") as mock:
        service = mock.return_value
        service.process_message = AsyncMock(return_value="Test response")
        yield service


@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test the chat endpoint flow"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Test data
        message_data = {
            "content": "Hello",
            "user_id": "test_user",
            "message_type": "text",
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Make request
        response = await client.post("/chat", json=message_data)

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_chat_service_process():
    """Test ChatService message processing"""
    chat_service = ChatService()

    # Test data
    message = "Hello"
    user_id = "test_user"
    history = [
        {
            "content": "Previous message",
            "sender": "user",
            "message_type": "text",
            "timestamp": datetime.utcnow().isoformat(),
        }
    ]

    # Process message
    response = await chat_service.process_message(message, user_id, history)

    # Verify response
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_history_formatting():
    """Test conversation history formatting"""
    chat_service = ChatService()

    # Test data
    history = [
        {
            "content": "User message",
            "sender": "user",
            "message_type": "text",
            "timestamp": datetime.utcnow().isoformat(),
        },
        {
            "content": "Assistant response",
            "sender": "assistant",
            "message_type": "text",
            "timestamp": datetime.utcnow().isoformat(),
        },
    ]

    # Format history
    formatted = chat_service._format_history(history)

    # Verify formatting
    assert len(formatted) == 2
    assert formatted[0].content == "User message"
    assert formatted[1].content == "Assistant response"


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in chat endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Invalid data
        invalid_data = {"user_id": "test_user"}  # Missing required fields

        # Make request
        response = await client.post("/chat", json=invalid_data)

        # Verify error response
        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_integration_flow(mock_db_client):
    """Test the complete integration flow"""
    chat_service = ChatService()

    # Test data
    message = "Hello"
    user_id = "test_user"

    # Mock DB responses
    mock_db_client.get_conversation_history.return_value = []

    # Process message
    response = await chat_service.process_message(message, user_id, [])

    # Verify flow
    assert isinstance(response, str)
    mock_db_client.get_conversation_history.assert_called_once_with(user_id)


def test_health_check():
    """Test health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
