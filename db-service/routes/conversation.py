from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime
from typing import List
from pymongo.errors import PyMongoError
from loguru import logger

from ..database import get_database
from ..models.conversation import Conversation, ConversationCreate, MessageCreate

router = APIRouter()


@router.post("/conversations/", response_model=Conversation)
async def create_conversation(
    conversation: ConversationCreate, db: AsyncIOMotorDatabase = Depends(get_database)
):
    try:
        conv_dict = conversation.dict()
        conv_dict["messages"] = []
        conv_dict["created_at"] = datetime.utcnow()
        conv_dict["updated_at"] = datetime.utcnow()

        result = await db.conversations.insert_one(conv_dict)
        created_conv = await db.conversations.find_one({"_id": result.inserted_id})
        logger.info(f"Created new conversation with ID: {result.inserted_id}")
        return created_conv
    except Exception as e:
        logger.error(f"Failed to create conversation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations/", response_model=List[Conversation])
async def get_conversations(
    skip: int = 0, limit: int = 20, db: AsyncIOMotorDatabase = Depends(get_database)
):
    conversations = await db.conversations.find().skip(skip).limit(limit).to_list(limit)
    return conversations


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(
    conversation_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    conversation = await db.conversations.find_one({"_id": ObjectId(conversation_id)})
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/conversations/{conversation_id}/messages")
async def add_message(
    conversation_id: str,
    message: MessageCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
):
    if not ObjectId.is_valid(conversation_id):
        logger.warning(f"Invalid conversation ID format: {conversation_id}")
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    message_dict = message.dict()
    message_dict["timestamp"] = datetime.utcnow()

    try:
        result = await db.conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {
                "$push": {"messages": message_dict},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )
    except PyMongoError as e:
        logger.error(f"Database error while adding message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if result.modified_count == 0:
        logger.warning(f"Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    logger.info(f"Added message to conversation {conversation_id}")
    return {"status": "success", "message": "Message added successfully"}


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str, db: AsyncIOMotorDatabase = Depends(get_database)
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID")

    result = await db.conversations.delete_one({"_id": ObjectId(conversation_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {"status": "success", "message": "Conversation deleted successfully"}
