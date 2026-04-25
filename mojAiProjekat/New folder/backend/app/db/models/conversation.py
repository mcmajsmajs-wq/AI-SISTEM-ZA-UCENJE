# -*- coding: utf-8 -*-
"""
================================================================================
CONVERSATION MODELS
================================================================================
Modeli za čuvanje chat konverzacija.

Verzija: 1.0.0
================================================================================
"""

from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Conversation(Base):
    """
    ================================================================================
    CONVERSATION MODEL
    ================================================================================
    Predstavlja jednu chat konverzaciju.
    """
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Conversation metadata
    title = Column(String(255), default="Nova konverzacija")
    provider = Column(String(50), default="auto")  # auto, openai, claude, deepseek, gemini, ollama
    is_active = Column(Boolean, default=True)
    
    # System prompt (optional)
    system_prompt = Column(Text, nullable=True)
    
    # Configuration
    thinking_enabled = Column(Boolean, default=False)
    enabled_tools = Column(JSON, nullable=True)  # List of enabled tool names
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship(
        "Message", 
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    
    def __repr__(self):
        return f"<Conversation {self.id} - {self.title}>"


class Message(Base):
    """
    ================================================================================
    MESSAGE MODEL
    ================================================================================
    Predstavlja jednu poruku u konverzaciji.
    """
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("conversations.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    
    # Tool calling
    tool_calls = Column(JSON, nullable=True)  # [{"id": "...", "name": "...", "arguments": {...}}]
    tool_results = Column(JSON, nullable=True)  # [{"tool_call_id": "...", "content": "..."}]
    
    # Metadata
    model = Column(String(100), nullable=True)
    provider = Column(String(50), nullable=True)
    thinking = Column(Text, nullable=True)  # Reasoning output (thinking mode)
    usage = Column(JSON, nullable=True)  # {"prompt_tokens": ..., "completion_tokens": ...}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self):
        return f"<Message {self.id} - {self.role}>"
