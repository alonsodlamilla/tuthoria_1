from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime


class Message(BaseModel):
    """Single message in a conversation"""
    content: str
    user_id: str
    context: Optional[Dict[str, str]] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    response: str
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationHistory(BaseModel):
    """Conversation history"""
    messages: List[Dict[str, str]]
    user_id: str 