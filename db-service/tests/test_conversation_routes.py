import pytest
from datetime import datetime
from bson import ObjectId

pytestmark = pytest.mark.asyncio

async def test_create_conversation(test_app):
    """Test creating a new conversation"""
    conversation_data = {
        "title": "Test Conversation",
        "participants": ["user1", "user2"]
    }
    
    response = test_app.post("/conversations/", json=conversation_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == conversation_data["title"]
    assert data["participants"] == conversation_data["participants"]
    assert "_id" in data
    assert "messages" in data
    assert len(data["messages"]) == 0
    assert "created_at" in data
    assert "updated_at" in data

async def test_get_conversations(test_app):
    """Test retrieving all conversations"""
    # Create two test conversations
    conversation_data1 = {
        "title": "Test Conversation 1",
        "participants": ["user1", "user2"]
    }
    conversation_data2 = {
        "title": "Test Conversation 2",
        "participants": ["user2", "user3"]
    }
    
    test_app.post("/conversations/", json=conversation_data1)
    test_app.post("/conversations/", json=conversation_data2)
    
    response = test_app.get("/conversations/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == conversation_data1["title"]
    assert data[1]["title"] == conversation_data2["title"]

async def test_get_conversation(test_app):
    """Test retrieving a specific conversation"""
    conversation_data = {
        "title": "Test Conversation",
        "participants": ["user1", "user2"]
    }
    
    # Create a conversation
    create_response = test_app.post("/conversations/", json=conversation_data)
    conversation_id = create_response.json()["_id"]
    
    # Get the conversation
    response = test_app.get(f"/conversations/{conversation_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["title"] == conversation_data["title"]
    assert data["participants"] == conversation_data["participants"]
    assert data["_id"] == conversation_id

async def test_add_message(test_app):
    """Test adding a message to a conversation"""
    # Create a conversation
    conversation_data = {
        "title": "Test Conversation",
        "participants": ["user1", "user2"]
    }
    create_response = test_app.post("/conversations/", json=conversation_data)
    conversation_id = create_response.json()["_id"]
    
    # Add a message
    message_data = {
        "content": "Hello, World!",
        "sender": "user1"
    }
    response = test_app.post(
        f"/conversations/{conversation_id}/messages",
        json=message_data
    )
    assert response.status_code == 200
    
    # Verify the message was added
    get_response = test_app.get(f"/conversations/{conversation_id}")
    data = get_response.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == message_data["content"]
    assert data["messages"][0]["sender"] == message_data["sender"]

async def test_delete_conversation(test_app):
    """Test deleting a conversation"""
    # Create a conversation
    conversation_data = {
        "title": "Test Conversation",
        "participants": ["user1", "user2"]
    }
    create_response = test_app.post("/conversations/", json=conversation_data)
    conversation_id = create_response.json()["_id"]
    
    # Delete the conversation
    response = test_app.delete(f"/conversations/{conversation_id}")
    assert response.status_code == 200
    
    # Verify the conversation was deleted
    get_response = test_app.get(f"/conversations/{conversation_id}")
    assert get_response.status_code == 404

async def test_invalid_conversation_id(test_app):
    """Test handling invalid conversation IDs"""
    invalid_id = "invalid_id"
    
    response = test_app.get(f"/conversations/{invalid_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid conversation ID"

async def test_nonexistent_conversation(test_app):
    """Test handling requests for nonexistent conversations"""
    nonexistent_id = str(ObjectId())
    
    response = test_app.get(f"/conversations/{nonexistent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Conversation not found" 