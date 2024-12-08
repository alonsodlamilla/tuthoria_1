import pytest
from datetime import datetime


@pytest.mark.asyncio
async def test_get_user_state_new_user(mock_db_service, sample_user_data):
    """Test get_user_state for new user"""
    state, context = await mock_db_service.get_user_state(sample_user_data["user_id"])

    assert state == "INICIO"
    assert context == {}


@pytest.mark.asyncio
async def test_get_user_state_existing_user(mock_db_service, sample_user_data):
    """Test get_user_state for existing user"""
    # First create a user state
    await mock_db_service.update_user_state(
        sample_user_data["user_id"],
        sample_user_data["current_state"],
        sample_user_data["context"],
    )

    state, context = await mock_db_service.get_user_state(sample_user_data["user_id"])

    assert state == sample_user_data["current_state"]
    assert context == sample_user_data["context"]


@pytest.mark.asyncio
async def test_update_user_state(mock_db_service, sample_user_data):
    """Test update_user_state"""
    await mock_db_service.update_user_state(
        sample_user_data["user_id"],
        sample_user_data["current_state"],
        sample_user_data["context"],
    )

    state, context = await mock_db_service.get_user_state(sample_user_data["user_id"])

    assert state == sample_user_data["current_state"]
    assert context == sample_user_data["context"]


@pytest.mark.asyncio
async def test_log_conversation(mock_db_service, sample_user_data):
    """Test log_conversation"""
    await mock_db_service.log_conversation(
        sample_user_data["user_id"],
        sample_user_data["message"],
        sample_user_data["response"],
    )

    history = await mock_db_service.get_conversation_history(
        sample_user_data["user_id"], limit=1
    )

    assert len(history) == 1
    assert history[0]["message"] == sample_user_data["message"]
    assert history[0]["response"] == sample_user_data["response"]


@pytest.mark.asyncio
async def test_get_conversation_history(
    mock_db_service, sample_user_data, sample_conversation_history
):
    """Test get_conversation_history"""
    # Log multiple conversations
    for conv in sample_conversation_history:
        await mock_db_service.log_conversation(
            sample_user_data["user_id"],
            conv["message"],
            conv["response"],
        )

    history = await mock_db_service.get_conversation_history(
        sample_user_data["user_id"]
    )

    assert len(history) == len(sample_conversation_history)
