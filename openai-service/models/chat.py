from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime


class Message(BaseModel):
    """Single message in a conversation"""

    content: str
    user_id: str
    message_type: str = "text"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatResponse(BaseModel):
    """Response from chat endpoint"""

    response: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationMessage(BaseModel):
    """Message in conversation history"""

    content: str
    sender: str
    message_type: str = "text"
    timestamp: datetime


class ConversationHistory(BaseModel):
    """Conversation history"""

    messages: List[ConversationMessage]
    user_id: str
