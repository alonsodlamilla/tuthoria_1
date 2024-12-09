import pytest
from unittest.mock import patch, AsyncMock
from services.db_client import DBClient


@pytest.fixture
async def db_client():
    client = DBClient()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_get_conversation_history():
    """Test conversation history retrieval"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"messages": [{"content": "test"}]}
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.get = AsyncMock(return_value=mock_response)

        client = DBClient()
        history = await client.get_conversation_history("test_user")

        assert isinstance(history, list)
        assert len(history) == 1


@pytest.mark.asyncio
async def test_store_message():
    """Test message storage"""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()

        mock_client.return_value.post = AsyncMock(return_value=mock_response)

        client = DBClient()
        success = await client.store_message("test_user", "test message")

        assert success is True
