"""Pydantic schemas for request/response models"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatRequest(BaseModel):
    message: str


class ChatMessage(BaseModel):
    id: Optional[int] = None
    role: str
    content: str
    timestamp: Optional[datetime] = None


class ChatResponse(BaseModel):
    message: str
    history: List[ChatMessage]


class StreamChunk(BaseModel):
    token: str
    done: bool = False