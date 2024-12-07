import pytest
from unittest.mock import Mock, patch
from services.chat_service import ChatService

@pytest.fixture
def mock_langchain_llm():
    with patch('langchain_openai.ChatOpenAI') as mock:
        yield mock

@pytest.fixture
def chat_service(mock_langchain_llm):
    return ChatService()

@pytest.mark.asyncio
async def test_process_message(chat_service, sample_user_data):
    """Test process_message method with LangChain"""
    # Mock the LangChain chain response
    mock_chain = Mock()
    mock_chain.arun.return_value = sample_user_data["response"]
    
    with patch('services.chat_service.LLMChain') as mock_llm_chain:
        mock_llm_chain.return_value = mock_chain
        
        response = await chat_service.process_message(
            message=sample_user_data["message"],
            current_state=sample_user_data["current_state"],
            context={
                "user_id": sample_user_data["user_id"],
                **sample_user_data["context"]
            }
        )
        
        assert response == sample_user_data["response"]
        mock_chain.arun.assert_called_once_with(input=sample_user_data["message"])