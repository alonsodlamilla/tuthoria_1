from fastapi import APIRouter, HTTPException
from models.conversation import ConversationMessage, Conversation
from database import get_database
from datetime import datetime
from bson import ObjectId

router = APIRouter()


@router.post("/conversations/messages")
async def add_message(message: ConversationMessage):
    try:
        # Get database connection
        db = await get_database()

        # Find existing conversation or create new one
        conversation = await db.conversations.find_one({"user_id": message.user_id})

        if not conversation:
            conversation = Conversation(
                user_id=message.user_id,
                messages=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            conversation_id = await db.conversations.insert_one(
                conversation.dict(by_alias=True)
            )
            conversation["_id"] = conversation_id.inserted_id

        # Add new message to conversation
        new_message = {
            "content": message.content,
            "sender": message.sender,
            "timestamp": message.timestamp,
            "message_type": message.message_type,
        }

        # Update conversation with new message
        result = await db.conversations.update_one(
            {"_id": ObjectId(conversation["_id"])},
            {
                "$push": {"messages": new_message},
                "$set": {"updated_at": datetime.utcnow()},
            },
        )

        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to store message")

        return {"status": "success", "message": "Message stored successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{user_id}")
async def get_conversation_history(user_id: str, limit: int = 10):
    try:
        # Get database connection
        db = await get_database()

        conversation = await db.conversations.find_one({"user_id": user_id})
        if not conversation:
            return {"messages": []}

        messages = conversation.get("messages", [])[-limit:]
        return {"messages": messages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
