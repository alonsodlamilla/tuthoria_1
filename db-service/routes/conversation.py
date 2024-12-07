from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, UTC
from typing import List
from loguru import logger

from database import get_database
from models.conversation import Conversation, ConversationMessage, Message

router = APIRouter()

@router.post("/conversations/messages")
async def add_message(
    message: ConversationMessage,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Store a new message in a conversation"""
    try:
        # Find or create conversation for this user
        conversation = await db.conversations.find_one({"user_id": message.user_id})
        
        if not conversation:
            conversation = {
                "user_id": message.user_id,
                "messages": [],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC)
            }
            await db.conversations.insert_one(conversation)
        
        # Add new message
        new_message = Message(
            content=message.content,
            sender=message.sender,
            timestamp=datetime.now(UTC)
        )
        
        await db.conversations.update_one(
            {"user_id": message.user_id},
            {
                "$push": {"messages": new_message.model_dump()},
                "$set": {"updated_at": datetime.now(UTC)}
            }
        )
        
        return {"status": "success", "message": "Message added successfully"}
    except Exception as e:
        logger.error(f"Error adding message: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to add message")

@router.get("/conversations/{user_id}")
async def get_conversation(
    user_id: str,
    limit: int = 10,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get conversation history for a user"""
    try:
        conversation = await db.conversations.find_one({"user_id": user_id})
        if not conversation:
            return {"messages": []}
            
        # Get last N messages
        messages = conversation.get("messages", [])[-limit:]
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")

@router.get("/conversations/{user_id}/latest")
async def get_latest_messages(
    user_id: str,
    limit: int = 5,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get latest messages for a user"""
    try:
        conversation = await db.conversations.find_one(
            {"user_id": user_id},
            {"messages": {"$slice": -limit}}
        )
        if not conversation:
            return {"messages": []}
            
        return {"messages": conversation.get("messages", [])}
    except Exception as e:
        logger.error(f"Error getting latest messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get latest messages")
