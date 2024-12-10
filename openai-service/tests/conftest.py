import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_app():
    """Mock FastAPI app for testing"""
    app = MagicMock()
    app.db_client = MagicMock()
    app.db_client.get_conversation_history = AsyncMock(return_value=[])
    app.chat_service = MagicMock()
    app.chat_service.process_message = AsyncMock(return_value="Test response")
    return app
