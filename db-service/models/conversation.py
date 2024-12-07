from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class Message(BaseModel):
    content: str
    sender: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


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
    id: Optional[str] = Field(alias="_id")
    messages: List[Message] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(BaseModel):
    content: str
    sender: str
