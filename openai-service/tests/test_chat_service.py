import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone
import sys

# Mock all langchain imports
mock_langchain = {
    "langchain_core.prompts": MagicMock(),
    "langchain_core.messages": MagicMock(),
    "langchain_openai": MagicMock(),
    "langchain_core.runnables": MagicMock(),
    "langchain_core.output_parsers": MagicMock(),
    "langchain_core.language_models": MagicMock(),
    "langchain_core.prompts.base": MagicMock(),
    "langchain_core.output_parsers.base": MagicMock(),
    "langchain_core.language_models.base": MagicMock(),
    "tiktoken": MagicMock(),
}

# Constants (copied from chat_service to avoid import issues)
MAX_TOKENS = 6000
SYSTEM_PROMPT_TOKENS = 200
BUFFER_TOKENS = 1000


@pytest.fixture(autouse=True)
def mock_imports():
    with patch.dict("sys.modules", mock_langchain):
        yield


@pytest.fixture
def mock_db_client():
    with patch("services.db_client.DBClient") as mock:
        client = mock.return_value
        client.get_conversation_history = AsyncMock(return_value=[])
        client.close = AsyncMock()
        yield client


@pytest.fixture
def chat_service(mock_db_client):
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        from services.chat_service import ChatService

        service = ChatService()
        # Mock internal methods and dependencies
        service._count_tokens = Mock(side_effect=lambda x: len(x))  # 1 token per char
        service.llm = MagicMock()
        service.llm.ainvoke = AsyncMock(return_value=MagicMock(content="Test response"))
        yield service


@pytest.mark.asyncio
async def test_init_success(chat_service):
    """Test successful initialization"""
    assert chat_service.db_client is not None
    assert chat_service.llm is not None
    assert chat_service.prompt is not None


@pytest.mark.asyncio
async def test_init_failure():
    """Test initialization failure"""
    with patch("services.db_client.DBClient", side_effect=Exception("DB Error")):
        from services.chat_service import ChatService

        with pytest.raises(Exception) as exc_info:
            ChatService()
        assert "DB Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_count_tokens(chat_service):
    """Test token counting"""
    text = "Hello, world!"
    token_count = chat_service._count_tokens(text)
    assert token_count == len(text)  # Our mock returns 1 token per char


@pytest.mark.asyncio
async def test_trim_history_empty(chat_service):
    """Test history trimming with empty history"""
    history = []
    trimmed = chat_service._trim_history_to_fit(history, "test message")
    assert trimmed == []


@pytest.mark.asyncio
async def test_trim_history_message_too_long(chat_service):
    """Test history trimming when message is too long"""
    history = [MagicMock(content="test")]
    long_message = "x" * (MAX_TOKENS + 1)  # Exceeds max tokens
    trimmed = chat_service._trim_history_to_fit(history, long_message)
    assert trimmed == []


@pytest.mark.asyncio
async def test_trim_history_partial(chat_service):
    """Test history trimming with partial history retention"""
    # Create messages that will exceed token limit
    messages = []
    for i in range(10):  # Create enough messages to exceed token limit
        msg = MagicMock()
        msg.content = "x" * 1000  # Each message is 1000 tokens
        messages.append(msg)

    trimmed = chat_service._trim_history_to_fit(messages, "new message")
    assert len(trimmed) < len(messages)
    # Check the most recent message is retained
    assert trimmed[-1].content == messages[-1].content


@pytest.mark.asyncio
async def test_format_history_empty(chat_service):
    """Test history formatting with empty history"""
    formatted = chat_service._format_history([])
    assert formatted == []


@pytest.mark.asyncio
async def test_format_history_invalid_messages(chat_service):
    """Test history formatting with invalid messages"""
    history = [
        {"content": None, "sender": "user"},  # Invalid content
        {"content": "test", "sender": "unknown"},  # Invalid sender
        {},  # Missing fields
    ]
    formatted = chat_service._format_history(history)
    assert formatted == []


@pytest.mark.asyncio
async def test_format_history_valid(chat_service):
    """Test history formatting with valid messages"""
    now = datetime.now(timezone.utc)
    history = [
        {
            "content": "Hello",
            "sender": "user",
            "timestamp": now,
            "message_type": "text",
        },
        {
            "content": "Hi there",
            "sender": "assistant",
            "timestamp": now,
            "message_type": "text",
        },
    ]

    # Mock the message classes for this specific test
    human_msg = MagicMock()
    human_msg.content = "Hello"
    ai_msg = MagicMock()
    ai_msg.content = "Hi there"

    with patch("services.chat_service.HumanMessage", return_value=human_msg), patch(
        "services.chat_service.AIMessage", return_value=ai_msg
    ):
        formatted = chat_service._format_history(history)
        assert len(formatted) == 2
        assert formatted[0].content == "Hello"
        assert formatted[1].content == "Hi there"


@pytest.mark.asyncio
async def test_process_message_success(chat_service):
    """Test successful message processing"""
    # Mock the LLM response
    chat_service.llm.ainvoke = AsyncMock(
        return_value=MagicMock(content="Test response")
    )

    message = "Hello"
    user_id = "test_user"
    history = [
        {
            "content": "Previous message",
            "sender": "user",
            "timestamp": datetime.now(timezone.utc),
            "message_type": "text",
        }
    ]

    response = await chat_service.process_message(message, user_id, history)
    assert response == "Test response"


@pytest.mark.asyncio
async def test_process_message_failure(chat_service):
    """Test message processing failure"""
    chat_service.llm.ainvoke = AsyncMock(side_effect=Exception("LLM Error"))

    with pytest.raises(Exception) as exc_info:
        await chat_service.process_message("test", "user123", [])
    assert "LLM Error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_close(chat_service):
    """Test service cleanup"""
    await chat_service.close()
    assert (
        chat_service.db_client.close.call_count == 1
    )  # Use call_count instead of assert_called_once


@pytest.mark.asyncio
async def test_count_tokens_error(chat_service):
    """Test token counting with error"""
    # Mock the encode method to raise an exception
    chat_service.tokenizer = MagicMock()
    chat_service.tokenizer.encode.side_effect = Exception("Tokenizer error")

    with pytest.raises(Exception) as exc_info:
        chat_service._count_tokens("test")
    assert "Tokenizer error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_format_history_error(chat_service):
    """Test history formatting with error"""
    # Create history that will cause an error when sorting
    malformed_history = [
        {
            "content": "Hello",
            "sender": "user",
            # Create a situation where timestamp access raises an error
            "timestamp": MagicMock(side_effect=Exception("Timestamp error")),
        }
    ]

    with pytest.raises(Exception) as exc_info:
        chat_service._format_history(malformed_history)
    assert "Error formatting history" in str(exc_info.value)
