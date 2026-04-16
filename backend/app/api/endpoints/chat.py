# -*- coding: utf-8 -*-
"""
================================================================================
CHAT API ENDPOINTS
================================================================================
Endpoint-i za AI Chat funkcionalnost.

Verzija: 1.0.0
================================================================================
"""

import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.conversation import Conversation, Message
from app.services.auth import get_current_user
from app.services.ai_chat import (
    AIChatService,
    ChatMessage,
    MessageRole,
    AVAILABLE_TOOLS,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================


class ChatRequest(BaseModel):
    """Request za chat endpoint."""

    message: str
    conversation_id: Optional[UUID] = None
    tools: Optional[List[str]] = None
    thinking: bool = False
    provider: str = "auto"
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    """Response za chat endpoint."""

    response: str
    conversation_id: UUID
    tool_calls: Optional[List[dict]] = None
    thinking: Optional[str] = None
    model: str
    provider: str
    usage: dict


class ConversationCreate(BaseModel):
    """Request za kreiranje nove konverzacije."""

    title: Optional[str] = "Nova konverzacija"
    provider: str = "auto"
    thinking_enabled: bool = False
    enabled_tools: Optional[List[str]] = None
    system_prompt: Optional[str] = None


class ConversationResponse(BaseModel):
    """Response za konverzaciju."""

    id: UUID
    title: str
    provider: str
    is_active: bool
    thinking_enabled: bool
    enabled_tools: Optional[List[str]] = None
    created_at: str
    updated_at: str
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Response za poruku."""

    id: UUID
    role: str
    content: str
    tool_calls: Optional[List[dict]] = None
    tool_results: Optional[List[dict]] = None
    thinking: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """Detalji konverzacije sa porukama."""

    id: UUID
    title: str
    provider: str
    is_active: bool
    thinking_enabled: bool
    enabled_tools: Optional[List[str]] = None
    created_at: str
    updated_at: str
    messages: List[MessageResponse] = []


class ProviderInfoResponse(BaseModel):
    """Informacije o provajderu."""

    id: str
    name: str
    available: bool
    supports_tools: bool
    supports_thinking: bool
    default_model: str


class ProvidersListResponse(BaseModel):
    """Lista svih provajdera."""

    providers: List[ProviderInfoResponse]


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CHAT ENDPOINT
    ================================================================================
    Šalje poruku AI i vraća odgovor.
    Kreira novu konverzaciju ili nastavlja postojeću.
    ================================================================================
    """
    logger.info(
        f"Chat request from user {current_user.email}: {request.message[:50]}..."
    )

    # Get or create conversation
    if request.conversation_id:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id,
            )
            .first()
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Konveracija nije pronađena",
            )
    else:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id,
            title=request.message[:50] + "..."
            if len(request.message) > 50
            else request.message,
            provider=request.provider,
            thinking_enabled=request.thinking,
            system_prompt=request.system_prompt,
            enabled_tools=request.tools,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Get user API keys
    user_api_keys = {
        "openai": current_user.ai_api_key_openai,
        "groq": current_user.ai_api_key_groq,
        "mistral": current_user.ai_api_key_mistral,
        "claude": current_user.ai_api_key_claude,
        "deepseek": current_user.ai_api_key_deepseek,
        "gemini": current_user.ai_api_key_gemini,
    }

    # Get conversation history
    db_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    messages = []

    # Add system prompt if exists
    if conversation.system_prompt:
        messages.append(
            ChatMessage(
                role=MessageRole.SYSTEM.value, content=conversation.system_prompt
            )
        )

    # Add conversation history
    for msg in db_messages:
        messages.append(ChatMessage(role=msg.role, content=msg.content))

    # Add current message
    messages.append(ChatMessage(role=MessageRole.USER.value, content=request.message))

    # Get enabled tools
    tool_names = request.tools or conversation.enabled_tools or []
    tools_enabled = (
        any(
            tool_name in AVAILABLE_TOOLS[0]["function"]["name"]
            for tool_name in tool_names
        )
        if tool_names
        else True
    )

    # Call AI service
    ai_service = AIChatService(user_api_keys=user_api_keys)

    try:
        response = await ai_service.chat(
            messages=messages,
            provider=request.provider,
            tools=tools_enabled,
            thinking=request.thinking,
            session=db,
            user_id=str(current_user.id),
        )
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Greška pri komunikaciji sa AI: {str(e)}",
        )

    # Save user message
    user_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.USER.value,
        content=request.message,
    )
    db.add(user_message)

    # Save AI response
    ai_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.ASSISTANT.value,
        content=response.content,
        tool_calls=[tc.__dict__ for tc in response.tool_calls]
        if response.tool_calls
        else None,
        model=response.model,
        provider=response.provider,
        thinking=response.thinking,
        usage=response.usage,
    )
    db.add(ai_message)

    # Update conversation
    conversation.updated_at = func.now()
    db.commit()

    return ChatResponse(
        response=response.content,
        conversation_id=conversation.id,
        tool_calls=[tc.__dict__ for tc in response.tool_calls]
        if response.tool_calls
        else None,
        thinking=response.thinking,
        model=response.model,
        provider=response.provider,
        usage=response.usage,
    )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CHAT STREAM ENDPOINT
    ================================================================================
    Šalje poruku AI i vraća streaming odgovor.
    ================================================================================
    """
    logger.info(f"Chat stream request from user {current_user.email}")

    async def generate():
        # Get or create conversation (same as above)
        if request.conversation_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == request.conversation_id,
                    Conversation.user_id == current_user.id,
                )
                .first()
            )

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Konveracija nije pronađena",
                )
        else:
            conversation = Conversation(
                user_id=current_user.id,
                title=request.message[:50] + "...",
                provider=request.provider,
                thinking_enabled=request.thinking,
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # Get conversation history
        db_messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation.id)
            .order_by(Message.created_at)
            .all()
        )

        messages = []
        if conversation.system_prompt:
            messages.append(
                ChatMessage(
                    role=MessageRole.SYSTEM.value, content=conversation.system_prompt
                )
            )

        for msg in db_messages:
            messages.append(ChatMessage(role=msg.role, content=msg.content))

        messages.append(
            ChatMessage(role=MessageRole.USER.value, content=request.message)
        )

        # Stream response
        user_api_keys = {
            "openai": current_user.ai_api_key_openai,
            "groq": current_user.ai_api_key_groq,
            "mistral": current_user.ai_api_key_mistral,
            "claude": current_user.ai_api_key_claude,
            "deepseek": current_user.ai_api_key_deepseek,
            "gemini": current_user.ai_api_key_gemini,
        }

        ai_service = AIChatService(user_api_keys=user_api_keys)

        full_response = ""
        async for chunk in ai_service.chat_stream(
            messages=messages,
            provider=request.provider,
            tools=False,  # No tools in streaming mode
            thinking=request.thinking,
        ):
            full_response += chunk
            yield f"data: {json.dumps({'content': chunk})}\n\n"

        # Save messages to DB
        user_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=request.message,
        )
        db.add(user_message)

        ai_message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=full_response,
            provider=request.provider,
        )
        db.add(ai_message)
        db.commit()

        yield f"data: {json.dumps({'done': True, 'conversation_id': str(conversation.id)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """
    ================================================================================
    LIST CONVERSATIONS
    ================================================================================
    Vraća listu konverzacija za trenutnog korisnika.
    ================================================================================
    """
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    result = []
    for conv in conversations:
        message_count = (
            db.query(Message).filter(Message.conversation_id == conv.id).count()
        )

        result.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                provider=conv.provider,
                is_active=conv.is_active,
                thinking_enabled=conv.thinking_enabled,
                enabled_tools=conv.enabled_tools,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                message_count=message_count,
            )
        )

    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    GET CONVERSATION
    ================================================================================
    Vraća detalje konverzacije sa svim porukama.
    ================================================================================
    """
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Konveracija nije pronađena"
        )

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
        .all()
    )

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        provider=conversation.provider,
        is_active=conversation.is_active,
        thinking_enabled=conversation.thinking_enabled,
        enabled_tools=conversation.enabled_tools,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                tool_results=m.tool_results,
                thinking=m.thinking,
                model=m.model,
                provider=m.provider,
                created_at=m.created_at.isoformat(),
            )
            for m in messages
        ],
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    DELETE CONVERSATION
    ================================================================================
    Briše konverzaciju.
    ================================================================================
    """
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id, Conversation.user_id == current_user.id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Konveracija nije pronađena"
        )

    db.delete(conversation)
    db.commit()

    return {"message": "Konveracija obrisana"}


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ================================================================================
    CREATE CONVERSATION
    ================================================================================
    Kreira novu praznu konverzaciju.
    ================================================================================
    """
    conversation = Conversation(
        user_id=current_user.id,
        title=request.title or "Nova konverzacija",
        provider=request.provider,
        thinking_enabled=request.thinking_enabled,
        enabled_tools=request.enabled_tools,
        system_prompt=request.system_prompt,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        provider=conversation.provider,
        is_active=conversation.is_active,
        thinking_enabled=conversation.thinking_enabled,
        enabled_tools=conversation.enabled_tools,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        message_count=0,
    )


@router.get("/providers", response_model=ProvidersListResponse)
async def get_providers(current_user: User = Depends(get_current_user)):
    """
    ================================================================================
    GET PROVIDERS
    ================================================================================
    Vraća listu dostupnih AI provajdera.
    ================================================================================
    """
    user_api_keys = {
        "openai": current_user.ai_api_key_openai,
        "groq": current_user.ai_api_key_groq,
        "mistral": current_user.ai_api_key_mistral,
        "claude": current_user.ai_api_key_claude,
        "deepseek": current_user.ai_api_key_deepseek,
        "gemini": current_user.ai_api_key_gemini,
    }

    ai_service = AIChatService(user_api_keys=user_api_keys)
    providers = ai_service.get_available_providers()

    return ProvidersListResponse(
        providers=[
            ProviderInfoResponse(
                id=p.id,
                name=p.name,
                available=p.available,
                supports_tools=p.supports_tools,
                supports_thinking=p.supports_thinking,
                default_model=p.default_model,
            )
            for p in providers
        ]
    )


@router.get("/tools")
async def get_tools():
    """
    ================================================================================
    GET TOOLS
    ================================================================================
    Vraća listu dostupnih alata.
    ================================================================================
    """
    return {"tools": AVAILABLE_TOOLS}
