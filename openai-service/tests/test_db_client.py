import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import httpx
from services.db_client import DBClient


@pytest.fixture(scope="function")
def mock_settings():
    with patch("services.db_client.get_settings") as mock:
        settings = MagicMock()
        settings.DB_SERVICE_URL = "http://test-db:8000/api/v1"
        mock.return_value = settings
        yield settings


@pytest.fixture(scope="function")
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        client = mock.return_value
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.aclose = AsyncMock()
        mock.return_value = client
        yield client


@pytest_asyncio.fixture(scope="function")
async def db_client(mock_settings, mock_httpx_client):
    client = DBClient()
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_init_success(mock_settings):
    """Test successful initialization"""
    client = DBClient()
    assert client.settings == mock_settings
    assert client.base_url == "http://test-db:8000/api/v1"
    await client.close()


@pytest.mark.asyncio
async def test_get_conversation_history_success(db_client, mock_httpx_client):
    """Test successful conversation history retrieval"""
    # Mock response data
    mock_messages = [
        {
            "content": "Hello",
            "sender": "user",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]
    mock_response = MagicMock()
    mock_response.json.return_value = {"messages": mock_messages}
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.get.return_value = mock_response

    # Test the method
    messages = await db_client.get_conversation_history("test_user", limit=10)

    # Verify results
    assert messages == mock_messages
    mock_httpx_client.get.assert_called_once_with(
        "http://test-db:8000/api/v1/conversations/test_user", params={"limit": 10}
    )


@pytest.mark.asyncio
async def test_get_conversation_history_http_error(db_client, mock_httpx_client):
    """Test conversation history retrieval with HTTP error"""
    # Mock HTTP error
    mock_httpx_client.get.side_effect = httpx.HTTPError("HTTP Error")

    # Test the method
    messages = await db_client.get_conversation_history("test_user")

    # Verify results
    assert messages == []
    mock_httpx_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_get_conversation_history_timeout(db_client, mock_httpx_client):
    """Test conversation history retrieval with timeout"""
    # Mock timeout error
    mock_httpx_client.get.side_effect = httpx.TimeoutException("Timeout")

    # Test the method
    messages = await db_client.get_conversation_history("test_user")

    # Verify results
    assert messages == []
    mock_httpx_client.get.assert_called_once()


@pytest.mark.asyncio
async def test_store_message_success(db_client, mock_httpx_client):
    """Test successful message storage"""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_httpx_client.post.return_value = mock_response

    # Test the method
    timestamp = datetime.now(timezone.utc)
    success = await db_client.store_message(
        user_id="test_user",
        content="Hello",
        sender="user",
        message_type="text",
        timestamp=timestamp,
    )

    # Verify results
    assert success is True
    mock_httpx_client.post.assert_called_once_with(
        "http://test-db:8000/api/v1/conversations/messages",
        json={
            "user_id": "test_user",
            "content": "Hello",
            "sender": "user",
            "message_type": "text",
            "timestamp": timestamp.isoformat(),
        },
        timeout=10.0,
    )


@pytest.mark.asyncio
async def test_store_message_retry_success(db_client, mock_httpx_client):
    """Test message storage with retry success"""
    # First call raises HTTPError, second call succeeds
    mock_success_response = MagicMock()
    mock_success_response.raise_for_status = MagicMock()  # No error

    mock_httpx_client.post.side_effect = [
        httpx.HTTPError("HTTP Error"),  # First call fails with HTTP error
        mock_success_response,  # Second call succeeds with valid response
    ]

    # Test the method
    success = await db_client.store_message(
        user_id="test_user", content="Hello", sender="user"
    )

    # Verify results
    assert success is True
    assert mock_httpx_client.post.call_count >= 2  # At least one retry


@pytest.mark.asyncio
async def test_store_message_all_retries_fail(db_client, mock_httpx_client):
    """Test message storage with all retries failing"""
    # Mock error response
    mock_error_response = MagicMock()
    mock_error_response.raise_for_status.side_effect = httpx.HTTPError("HTTP Error")

    # All calls will fail
    mock_httpx_client.post.return_value = mock_error_response

    # Test the method
    success = await db_client.store_message(
        user_id="test_user", content="Hello", sender="user"
    )

    # Verify results
    assert success is False
    assert mock_httpx_client.post.call_count >= 1  # At least one attempt


@pytest.mark.asyncio
async def test_store_message_timeout(db_client, mock_httpx_client):
    """Test message storage with timeout"""
    # Mock timeout error
    mock_httpx_client.post.side_effect = httpx.TimeoutException("Timeout")

    # Test the method
    success = await db_client.store_message(
        user_id="test_user", content="Hello", sender="user"
    )

    # Verify results
    assert success is False
    assert mock_httpx_client.post.call_count >= 1  # At least one attempt


@pytest.mark.asyncio
async def test_close(db_client, mock_httpx_client):
    """Test client cleanup"""
    await db_client.close()
    mock_httpx_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_close_with_error(db_client, mock_httpx_client):
    """Test client cleanup with error"""
    # Mock aclose to raise an error
    mock_httpx_client.aclose.side_effect = [Exception("Close error")]

    # The close method should handle the error gracefully
    await db_client.close()

    # Verify the close was attempted
    mock_httpx_client.aclose.assert_called_once()
