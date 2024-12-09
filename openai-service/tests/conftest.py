import pytest
from fastapi.testclient import TestClient
import mongomock
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from app import app
from services.chat_service import ChatService
from services.db_client import DBClient


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
def mock_db_client(mock_mongo):
    """Mocked DB client"""
    with patch("services.db_client.MongoClient") as mock_client:
        mock_client.return_value = mock_mongo
        db_client = DBClient()
        yield db_client


@pytest.fixture
def mock_chat_service():
    """Mocked Chat service"""
    with patch("services.chat_service.ChatOpenAI") as mock_llm:
        # Create a mock chain that returns a string response
        mock_chain = MagicMock()
        mock_chain.ainvoke = MagicMock()
        mock_chain.ainvoke.return_value = "Test response"

        # Create the chat service and replace its chain
        chat_service = ChatService()
        chat_service.chain = mock_chain
        yield chat_service


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
