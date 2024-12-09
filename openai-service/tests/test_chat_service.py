import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from services.chat_service import ChatService
from langchain_core.messages import HumanMessage, AIMessage


@pytest.mark.asyncio
async def test_process_message_success():
    """Test successful message processing"""
    with patch("services.chat_service.ChatOpenAI") as mock_llm_class:
        # Create a mock LLM instance with async capabilities
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        # Create a mock response
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.ainvoke.return_value = mock_response

        # Create service and test
        chat_service = ChatService()
        message = "Hello"
        user_id = "test_user"
        history = [{"message": "Hi", "response": "Hello!"}]

        response = await chat_service.process_message(message, user_id, history)
        assert isinstance(response, str)
        assert response == "Test response"

        # Verify the mock was called with correct arguments
        mock_llm.ainvoke.assert_called_once()
        call_args = mock_llm.ainvoke.call_args[0][0]
        assert "chat_history" in call_args
        assert "input" in call_args
        assert call_args["input"] == message


def test_format_history():
    """Test history formatting"""
    chat_service = ChatService()
    history = [{"message": "Hi", "response": "Hello!"}]

    formatted = chat_service._format_history(history)
    assert len(formatted) == 2
    assert isinstance(formatted[0], HumanMessage)
    assert isinstance(formatted[1], AIMessage)
