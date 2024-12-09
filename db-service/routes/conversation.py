from fastapi import APIRouter, HTTPException
from models.conversation import ConversationMessage, Conversation, Message
from database import get_database
from datetime import datetime
from bson import ObjectId
from loguru import logger


router = APIRouter()


@router.post("/conversations/messages")
async def add_message(message: ConversationMessage):
    try:
        # Get database connection
        db = await get_database()

        # Log incoming message details
        logger.info(f"Processing message for user: {message.user_id}")

        try:
            # Find existing conversation or create new one
            conversation = await db.conversations.find_one({"user_id": message.user_id})

            if not conversation:
                logger.info(f"Creating new conversation for user: {message.user_id}")
                # Create new conversation with default title and participants
                new_conversation = Conversation(
                    user_id=message.user_id,
                    title=f"Chat with {message.user_id}",
                    participants=[message.user_id],
                    messages=[],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )

                # Insert the new conversation
                insert_result = await db.conversations.insert_one(
                    new_conversation.model_dump(by_alias=True)
                )
                if not insert_result.inserted_id:
                    raise HTTPException(
                        status_code=500, detail="Failed to create conversation"
                    )

                conversation_id = insert_result.inserted_id
                logger.info(f"Created new conversation with ID: {conversation_id}")
            else:
                conversation_id = conversation["_id"]
                logger.info(f"Using existing conversation: {conversation_id}")

            # Create new message
            new_message = Message(
                content=message.content,
                sender=message.sender,
                timestamp=message.timestamp,
                message_type=message.message_type,
            )

            # Update conversation with new message
            update_result = await db.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {
                    "$push": {"messages": new_message.model_dump()},
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )

            if update_result.modified_count == 0:
                logger.error(f"Failed to update conversation: {conversation_id}")
                raise HTTPException(status_code=500, detail="Failed to store message")

            logger.info(f"Successfully stored message for user: {message.user_id}")
            return {"status": "success", "message": "Message stored successfully"}

        except Exception as e:
            logger.error(f"Database operation error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Database operation failed: {str(e)}"
            )

    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10):
    try:
        logger.info(f"Fetching conversation history for user: {user_id}")
        db = await get_database()

        conversation = await db.conversations.find_one({"user_id": user_id})
        if not conversation:
            logger.info(f"No conversation found for user: {user_id}")
            return {"messages": []}

        messages = conversation.get("messages", [])[-limit:]
        logger.info(f"Retrieved {len(messages)} messages for user: {user_id}")
        return {"messages": messages}

    except Exception as e:
        logger.error(f"Error fetching conversation history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
