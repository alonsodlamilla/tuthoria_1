import pytest
from fastapi.testclient import TestClient
import mongomock
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from app import app
from services.chat_service import ChatService
from services.db_service import DBService


@pytest.fixture
def test_app():
    """Test app with mocked dependencies"""
    app.dependency_overrides = {}
    return TestClient(app)


@pytest.fixture
def mock_mongo():
    """Mock MongoDB client"""
    return mongomock.MongoClient()


@pytest.fixture
def mock_db_service(mock_mongo):
    """Mocked DB service"""
    with patch("services.db_service.MongoClient") as mock_client:
        mock_client.return_value = mock_mongo
        db_service = DBService()
        yield db_service


@pytest.fixture
def mock_chat_service():
    """Mocked Chat service"""
    with patch("services.chat_service.OpenAI"), patch(
        "services.chat_service.ChatOpenAI"
    ):
        chat_service = ChatService()
        chat_service.get_completion = MagicMock()
        chat_service.get_langchain_response = MagicMock()
        yield chat_service


@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        "user_id": "test_user_123",
        "message": "Hello, how are you?",
        "response": "I'm doing well, thank you!",
        "current_state": "INICIO",
        "context": {
            "anio": "3° año",
            "curso": "Matemática",
            "seccion": "A",
        },
    }


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history"""
    return [
        {
            "message": "Hello",
            "response": "Hi there!",
            "created_at": datetime.utcnow(),
        },
        {
            "message": "How are you?",
            "response": "I'm good, thanks!",
            "created_at": datetime.utcnow(),
        },
    ]
