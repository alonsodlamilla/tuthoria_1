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


class ConversationBase(BaseModel):
    title: Optional[str] = None
    participants: List[str] = Field(default_factory=list)
    user_id: str

    @field_validator("title")
    @classmethod
    def set_default_title(cls, v, values):
        if v is None and "user_id" in values:
            return f"Chat with {values['user_id']}"
        return v

    @field_validator("participants")
    @classmethod
    def set_default_participants(cls, v, values):
        if not v and "user_id" in values:
            return [values["user_id"]]
        return v


class Conversation(ConversationBase):
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str}
        populate_by_name = True
        arbitrary_types_allowed = True


class MessageCreate(BaseModel):
    content: str
    sender: str
