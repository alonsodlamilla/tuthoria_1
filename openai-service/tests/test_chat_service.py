import pytest
from services.chat_service import ChatService


def test_chat_service_initialization():
    """Test ChatService initialization"""
    with pytest.raises(ValueError):
        ChatService()  # Should raise error when OPENAI_API_KEY is not set


@pytest.mark.asyncio
async def test_get_completion(mock_chat_service, sample_user_data):
    """Test get_completion method"""
    mock_chat_service.get_completion.return_value = sample_user_data["response"]

    response = await mock_chat_service.get_completion(
        sample_user_data["message"], sample_user_data["user_id"]
    )

    assert response == sample_user_data["response"]


@pytest.mark.asyncio
async def test_get_langchain_response(mock_chat_service, sample_user_data):
    """Test get_langchain_response method"""
    mock_chat_service.get_langchain_response.return_value = sample_user_data["response"]

    response = await mock_chat_service.get_langchain_response(
        sample_user_data["message"],
        sample_user_data["current_state"],
        sample_user_data["context"],
    )

    assert response == sample_user_data["response"]
