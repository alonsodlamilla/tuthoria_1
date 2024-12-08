import pytest
from fastapi import HTTPException
from datetime import datetime


def test_chat_endpoint_success(
    test_app, mock_chat_service, mock_db_service, sample_user_data
):
    """Test successful chat request"""
    mock_chat_service.get_completion.return_value = sample_user_data["response"]

    response = test_app.post(
        "/chat",
        json={
            "message": sample_user_data["message"],
            "user_id": sample_user_data["user_id"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"response": sample_user_data["response"]}


def test_chat_endpoint_error(test_app, mock_chat_service):
    """Test chat request with error"""
    mock_chat_service.get_completion.side_effect = Exception("Test error")

    response = test_app.post(
        "/chat",
        json={"message": "Hello", "user_id": "test_user"},
    )

    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]


def test_get_response_gpt_success(
    test_app, mock_chat_service, mock_db_service, sample_user_data
):
    """Test successful GPT response request"""
    mock_chat_service.get_langchain_response.return_value = sample_user_data["response"]

    response = test_app.get(
        "/getresponsegpt",
        params={
            "user_prompt": sample_user_data["message"],
            "user_id": sample_user_data["user_id"],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"response": sample_user_data["response"]}


def test_get_history_success(test_app, mock_db_service, sample_conversation_history):
    """Test successful history retrieval"""
    mock_db_service.get_conversation_history.return_value = sample_conversation_history

    response = test_app.get("/history/test_user_123")

    assert response.status_code == 200
    assert len(response.json()) == len(sample_conversation_history)


def test_get_history_with_limit(test_app, mock_db_service, sample_conversation_history):
    """Test history retrieval with custom limit"""
    mock_db_service.get_conversation_history.return_value = sample_conversation_history[
        :1
    ]

    response = test_app.get("/history/test_user_123?limit=1")

    assert response.status_code == 200
    assert len(response.json()) == 1
