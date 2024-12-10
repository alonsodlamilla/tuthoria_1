from fastapi import APIRouter, HTTPException
from models.conversation import ConversationMessage, Conversation, Message
from database import get_database
from datetime import datetime
from bson import ObjectId
from loguru import logger
from typing import List, Dict


router = APIRouter()


@router.post("/conversations/messages")
async def add_message(message: ConversationMessage):
    try:
        # Get database connection
        db = await get_database()

        # Log incoming message details
        logger.info(f"Processing message for user: {message.user_id}")

        # Find existing conversation or create new one
        conversation = await db.conversations.find_one({"user_id": message.user_id})

        # Create new message object
        new_message = Message(
            content=message.content,
            sender=message.sender,
            timestamp=message.timestamp,
            message_type=message.message_type,
        )

        if not conversation:
            logger.info(f"Creating new conversation for user: {message.user_id}")
            # Create new conversation with default title and participants
            new_conversation = Conversation(
                user_id=message.user_id,
                title=f"Chat with {message.user_id}",
                participants=[message.user_id],
                messages=[new_message],  # Include the first message
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            try:
                # Insert the new conversation with the message
                result = await db.conversations.insert_one(
                    new_conversation.model_dump(by_alias=True)
                )
                if not result.inserted_id:
                    logger.error("Failed to create new conversation")
                    raise HTTPException(
                        status_code=500, detail="Failed to create conversation"
                    )
                logger.info(f"Created new conversation with ID: {result.inserted_id}")
                return {"status": "success", "message": "Message stored successfully"}
            except Exception as e:
                logger.error(f"Error creating conversation: {str(e)}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to create conversation: {str(e)}"
                )
        else:
            # Conversation exists, update it with the new message
            try:
                if "_id" not in conversation:
                    logger.error("Conversation found but missing _id field")
                    raise HTTPException(
                        status_code=500, detail="Invalid conversation data"
                    )

                conversation_id = conversation["_id"]
                logger.info(f"Updating existing conversation: {conversation_id}")

                # Update conversation with new message
                update_result = await db.conversations.update_one(
                    {"_id": conversation_id},
                    {
                        "$push": {"messages": new_message.model_dump()},
                        "$set": {"updated_at": datetime.utcnow()},
                    },
                )

                if update_result.modified_count == 0:
                    logger.error(f"Failed to update conversation: {conversation_id}")
                    raise HTTPException(
                        status_code=500, detail="Failed to store message"
                    )

                logger.info(f"Successfully stored message for user: {message.user_id}")
                return {"status": "success", "message": "Message stored successfully"}

            except Exception as e:
                logger.error(f"Error updating conversation: {str(e)}")
                raise HTTPException(
                    status_code=500, detail=f"Failed to update conversation: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10):
    """Get conversation history for a user with proper message formatting"""
    try:
        logger.info(f"Fetching conversation history for user: {user_id}")
        db = await get_database()

        # Find conversation
        conversation = await db.conversations.find_one({"user_id": user_id})
        if not conversation:
            logger.info(f"No conversation found for user: {user_id}")
            return {"messages": []}

        # Get messages and validate/format them
        raw_messages = conversation.get("messages", [])[-limit:]
        formatted_messages = []

        for msg in raw_messages:
            try:
                # Ensure message has all required fields
                message = Message(
                    content=msg["content"],
                    sender=msg["sender"],
                    timestamp=msg["timestamp"],
                    message_type=msg.get("message_type", "text"),
                )
                formatted_messages.append(message.model_dump())
            except Exception as e:
                logger.warning(f"Skipping invalid message: {str(e)}")
                continue

        logger.info(
            f"Retrieved and formatted {len(formatted_messages)} messages for user: {user_id}"
        )
        return {"messages": formatted_messages}

    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
