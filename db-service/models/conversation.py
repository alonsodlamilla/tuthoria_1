from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class PyObjectId(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            if not isinstance(v, ObjectId):
                raise ValueError("Invalid ObjectId")
        return str(v)


class Message(BaseModel):
    content: str
    sender: str  # user_id or "assistant"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = "text"


class ConversationMessage(BaseModel):
    user_id: str
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: str = "text"


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    participants: List[str] = Field(..., min_items=1)

    @field_validator("participants")
    @classmethod
    def validate_participants(cls, v):
        if not all(isinstance(p, str) and p.strip() for p in v):
            raise ValueError("All participants must be non-empty strings")
        return v


class Conversation(ConversationCreate):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: str
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True


class MessageCreate(BaseModel):
    content: str
    sender: str
