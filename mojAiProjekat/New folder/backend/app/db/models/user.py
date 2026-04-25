# -*- coding: utf-8 -*-
"""
================================================================================
SQLALCHEMY MODELS - USER
================================================================================
Verzija: 1.0.0
================================================================================
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class User(Base):
    """
    ================================================================================
    USER MODEL
    ================================================================================
    Reprezentuje korisnika u sistemu.
    ================================================================================
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # Status polja
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(Enum("admin", "user", name="user_role"), default="user")
    
    # Preference
    timezone = Column(String(50), default="Europe/Belgrade")
    language = Column(String(10), default="sr")
    
    # AI podešavanja
    ai_provider = Column(String(50), default="auto")  # auto | ollama | openai | claude | gemini | groq | mistral | deepseek | custom
    ai_api_key_openai = Column(Text, nullable=True)
    ai_api_key_claude = Column(Text, nullable=True)
    ai_api_key_gemini = Column(Text, nullable=True)
    ai_api_key_groq = Column(Text, nullable=True)
    ai_api_key_mistral = Column(Text, nullable=True)
    ai_api_key_deepseek = Column(Text, nullable=True)
    ai_custom_base_url = Column(String(500), nullable=True)
    ai_api_key_custom = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"


class UserSession(Base):
    """
    ================================================================================
    USER SESSION MODEL
    ================================================================================
    Reprezentuje aktivnu sesiju korisnika.
    ================================================================================
    """
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    token = Column(Text, nullable=False)
    refresh_token = Column(Text)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
