# -*- coding: utf-8 -*-
"""
================================================================================
Petar II Petrović-Njegoš
"Blago tome ko dovijek živi, imao se rašta i roditi"
================================================================================

AI Learning System
ai_chat.py
Verzija: 1.0.0
Autor: Branko Suznjevic
Datum: 2026

Funkcionalnosti:
- Unified AI Chat Service
- Multi-provider: OpenAI, Claude, DeepSeek, Gemini, Ollama
- Multi-turn chat
- Tool calling
- Streaming
================================================================================
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# ENUMS AND DATA CLASSES
# ============================================================


# ============================================================
# VALID MODELS - Auto-provera aktuelnih modela
# ============================================================

VALID_MODELS = {
    "openai": "gpt-4o",
    "groq": "llama-3.3-70b-versatile",
    "mistral": "mistral-small-latest",
    "deepseek": "deepseek-chat",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.1",
}


def get_valid_model(provider: str, fallback: str = None) -> str:
    """Vrati validan model za provider."""
    return VALID_MODELS.get(provider, fallback or "gpt-4o")


# ============================================================
# RECOVERABLE ERRORS - Automatski fallback
# ============================================================

RECOVERABLE_ERRORS = [
    "429",
    "rate_limit",
    "rate limit",
    "402",
    "401",
    "unauthorized",
    "invalid_api_key",
    "decommissioned",
    "model no longer",
    "insufficient",
    "quota",
    "too many requests",
    "rate limit exceeded",
    "rate limit error",
]


def is_recoverable_error(error: str, status_code: int = None) -> bool:
    """Proveri da li je greška recoveriable."""
    if status_code and status_code in [401, 402, 403, 429]:
        return True
    error_lower = error.lower()
    return any(x in error_lower for x in RECOVERABLE_ERRORS)


# ============================================================
# PROVIDER ENUM
# ============================================================


class AIProvider(str, Enum):
    AUTO = "auto"
    OPENAI = "openai"
    GROQ = "groq"
    MISTRAL = "mistral"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ToolResult:
    tool_call_id: str
    content: str
    is_error: bool = False


@dataclass
class ChatResponse:
    content: str
    tool_calls: Optional[List[ToolCall]] = None
    thinking: Optional[str] = None
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


@dataclass
class ProviderInfo:
    id: str
    name: str
    available: bool
    supports_tools: bool
    supports_thinking: bool
    default_model: str


# ============================================================
# TOOL DEFINITIONS
# ============================================================

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Pretraživanje baze znanja. Koristi ovaj alat kada "  # noqa: E501
            "korisnik pita o opštim temama ili traži informacije.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Upit za pretragu"},
                    "top_k": {
                        "type": "integer",
                        "description": "Broj rezultata (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "translate_text",
            "description": "Prevođenje teksta između jezika.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Tekst za prevod"},
                    "target_lang": {
                        "type": "string",
                        "description": "Ciljni jezik (en, sr, de, fr, es, it, etc.)",
                    },
                    "source_lang": {
                        "type": "string",
                        "description": "Izvorni jezik (auto za automatsko prepoznavanje)",
                        "default": "auto",
                    },
                },
                "required": ["text", "target_lang"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_quiz",
            "description": "Generisanje kviza iz dokumenta. Koristi kada korisnik želi da generiše pitanja za učenje.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID dokumenta za generisanje kviza",
                    },
                    "num_questions": {
                        "type": "integer",
                        "description": "Broj pitanja (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_summary",
            "description": "Kratki rezime dokumenta. Koristi kada korisnik želi sažetak dokumenta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "ID dokumenta"}
                },
                "required": ["document_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Pretraga korisničkih dokumenata po sadržaju.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Upit za pretragu"},
                    "limit": {
                        "type": "integer",
                        "description": "Broj rezultata (default: 10)",
                        "default": 10,
                    },
                },
                "required": ["query"],
            },
        },
    },
]


# ============================================================
# BASE CLIENT
# ============================================================


class BaseAIChatClient(ABC):
    @abstractmethod
    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        pass

    @abstractmethod
    def is_available(self) -> bool:
        pass


# ============================================================
# OPENAI CLIENT
# ============================================================


class OpenAIChatClient(BaseAIChatClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 120,
    ):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return AIProvider.OPENAI.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _convert_messages(self, messages: List[ChatMessage]) -> List[Dict]:
        result = []
        for msg in messages:
            if msg.role == MessageRole.TOOL.value:
                result.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.tool_call_id,
                    }
                )
            else:
                item = {"role": msg.role, "content": msg.content}
                if msg.name:
                    item["name"] = msg.name
                if msg.tool_calls:
                    item["tool_calls"] = msg.tool_calls
                result.append(item)
        return result

    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        if not self.api_key:
            return ChatResponse(
                content="OpenAI API key nije konfigurisan", provider=self.provider_name
            )

        # Select model based on thinking mode
        model = self.model
        if thinking and "o1" not in model:
            model = "o1-preview"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": 0.7 if not thinking else 1.0,
        }

        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()

                message = data["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = None

                if message.get("tool_calls"):
                    tool_calls = [
                        ToolCall(
                            id=tc["id"],
                            name=tc["function"]["name"],
                            arguments=json.loads(tc["function"]["arguments"]),
                        )
                        for tc in message["tool_calls"]
                    ]

                usage = data.get("usage", {})

                return ChatResponse(
                    content=content,
                    tool_calls=tool_calls,
                    model=data.get("model", model),
                    provider=self.provider_name,
                    usage={
                        "prompt_tokens": usage.get("prompt_tokens", 0),
                        "completion_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0),
                    },
                )
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_str = str(e)
                if is_recoverable_error(error_str, status_code):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable HTTP error {status_code}: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"OpenAI chat HTTP error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa OpenAI: {str(e)}",
                    provider=self.provider_name,
                )
            except Exception as e:
                error_str = str(e)
                if is_recoverable_error(error_str):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable error: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"OpenAI chat error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa OpenAI: {str(e)}",
                    provider=self.provider_name,
                )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        # Thinking mode doesn't support streaming
        if thinking:
            response = await self.chat(messages, tools, thinking=False)
            yield response.content
            return

        if not self.api_key:
            yield "OpenAI API key nije konfigurisan"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": self._convert_messages(messages),
            "temperature": 0.7,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            pass


# ============================================================
# DEEPSEEK CLIENT
# ============================================================


class DeepSeekChatClient(BaseAIChatClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "deepseek-chat",
        base_url: str = "https://api.deepseek.com/v1",
        timeout: int = 120,
    ):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model
        self.base_url = base_url
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return AIProvider.DEEPSEEK.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        if not self.api_key:
            return ChatResponse(
                content="DeepSeek API key nije konfigurisan",
                provider=self.provider_name,
            )

        # Use reasoner model for thinking
        model = "deepseek-reasoner" if thinking else self.model

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        msg_list = [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": model,
            "messages": msg_list,
            "temperature": 0.7,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=payload
                )
                response.raise_for_status()
                data = response.json()

                message = data["choices"][0]["message"]
                content = message.get("content", "")
                tool_calls = None

                if message.get("tool_calls"):
                    tool_calls = [
                        ToolCall(
                            id=tc["id"],
                            name=tc["function"]["name"],
                            arguments=json.loads(tc["function"]["arguments"]),
                        )
                        for tc in message["tool_calls"]
                    ]

                # DeepSeek reasoner returns thinking in reasoning_content
                thinking_content = message.get("reasoning_content")

                return ChatResponse(
                    content=content,
                    tool_calls=tool_calls,
                    thinking=thinking_content,
                    model=data.get("model", model),
                    provider=self.provider_name,
                    usage=data.get("usage", {}),
                )
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_str = str(e)
                if is_recoverable_error(error_str, status_code):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable HTTP error {status_code}: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"DeepSeek chat HTTP error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa DeepSeek: {str(e)}",
                    provider=self.provider_name,
                )
            except Exception as e:
                error_str = str(e)
                if is_recoverable_error(error_str):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable error: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"DeepSeek chat error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa DeepSeek: {str(e)}",
                    provider=self.provider_name,
                )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        if thinking:
            response = await self.chat(messages, tools, thinking=False)
            yield response.content
            return

        if not self.api_key:
            yield "DeepSeek API key nije konfigurisan"
            return

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        msg_list = [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": self.model,
            "messages": msg_list,
            "temperature": 0.7,
            "stream": True,
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except Exception:
                            pass


# ============================================================
# CLAUDE CLIENT
# ============================================================


class ClaudeChatClient(BaseAIChatClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        timeout: int = 120,
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return AIProvider.CLAUDE.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        if not self.api_key:
            return ChatResponse(
                content="Claude API key nije konfigurisan", provider=self.provider_name
            )

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        # Convert messages format
        msg_list = []
        for msg in messages:
            if msg.role == MessageRole.SYSTEM.value:
                msg_list.append({"role": "user", "content": msg.content})
                msg_list.append({"role": "assistant", "content": "Razumem."})
            else:
                msg_list.append({"role": msg.role, "content": msg.content})

        payload = {
            "model": self.model,
            "messages": msg_list,
            "max_tokens": 4096,
            "temperature": 0.7,
        }

        if tools:
            # Convert OpenAI tools format to Claude
            payload["tools"] = tools

        if thinking:
            payload["extra_headers"] = {
                "anthropic-beta": "extended-thinking-2025-01-20"
            }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

                content = ""
                tool_calls = None

                for block in data.get("content", []):
                    if block.get("type") == "text":
                        content += block.get("text", "")
                    elif block.get("type") == "tool_use":
                        tool_calls = tool_calls or []
                        tool_calls.append(
                            ToolCall(
                                id=block.get("id", ""),
                                name=block.get("name", ""),
                                arguments=block.get("input", {}),
                            )
                        )

                usage = data.get("usage", {})

                return ChatResponse(
                    content=content,
                    tool_calls=tool_calls,
                    model=data.get("model", self.model),
                    provider=self.provider_name,
                    usage={
                        "input_tokens": usage.get("input_tokens", 0),
                        "output_tokens": usage.get("output_tokens", 0),
                    },
                )
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_str = str(e)
                if is_recoverable_error(error_str, status_code):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable HTTP error {status_code}: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Claude chat HTTP error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Claude: {str(e)}",
                    provider=self.provider_name,
                )
            except Exception as e:
                error_str = str(e)
                if is_recoverable_error(error_str):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable error: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Claude chat error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Claude: {str(e)}",
                    provider=self.provider_name,
                )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        # Claude doesn't support streaming with tools
        response = await self.chat(messages, tools, thinking=False)
        yield response.content


# ============================================================
# GEMINI CLIENT
# ============================================================


class GeminiChatClient(BaseAIChatClient):
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash",
        timeout: int = 120,
    ):
        self.api_key = api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return AIProvider.GEMINI.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        if not self.api_key:
            return ChatResponse(
                content="Gemini API key nije konfigurisan", provider=self.provider_name
            )

        # Select model
        if thinking and "thinking" not in self.model:
            model = "gemini-2.0-flash-thinking"
        else:
            model = self.model

        # Convert messages
        contents = []
        for msg in messages:
            if msg.role == MessageRole.USER.value:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})
            elif msg.role == MessageRole.ASSISTANT.value:
                contents.append({"role": "model", "parts": [{"text": msg.content}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
        }

        if tools:
            payload["tools"] = tools

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                candidate = data.get("candidates", [{}])[0]
                content = candidate.get("content", {})
                parts = content.get("parts", [{}])

                text = ""
                tool_calls = None

                for part in parts:
                    if "text" in part:
                        text += part["text"]
                    elif "functionCall" in part:
                        fc = part["functionCall"]
                        tool_calls = tool_calls or []
                        tool_calls.append(
                            ToolCall(
                                id=fc.get("name", ""),
                                name=fc.get("name", ""),
                                arguments=fc.get("args", {}),
                            )
                        )

                # Extract thinking if available
                thinking_content = None
                if thinking:
                    usage_metadata = data.get("usageMetadata", {})
                    thinking_tokens = usage_metadata.get("thoughtsTokenCount", 0)
                    if thinking_tokens > 0:
                        thinking_content = "(Thinking process included)"

                return ChatResponse(
                    content=text,
                    tool_calls=tool_calls,
                    thinking=thinking_content,
                    model=model,
                    provider=self.provider_name,
                    usage={},
                )
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_str = str(e)
                if is_recoverable_error(error_str, status_code):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable HTTP error {status_code}: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Gemini chat HTTP error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Gemini: {str(e)}",
                    provider=self.provider_name,
                )
            except Exception as e:
                error_str = str(e)
                if is_recoverable_error(error_str):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable error: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Gemini chat error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Gemini: {str(e)}",
                    provider=self.provider_name,
                )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        if thinking:
            response = await self.chat(messages, tools, thinking=False)
            yield response.content
            return

        if not self.api_key:
            yield "Gemini API key nije konfigurisan"
            return

        contents = []
        for msg in messages:
            if msg.role == MessageRole.USER.value:
                contents.append({"role": "user", "parts": [{"text": msg.content}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"  # noqa: E501

        payload = {
            "contents": contents,
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8192},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        try:
                            chunk = json.loads(data)
                            part = (
                                chunk.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [{}])[0]
                            )
                            text = part.get("text", "")
                            if text:
                                yield text
                        except Exception:
                            pass


# ============================================================
# OLLAMA CLIENT
# ============================================================


class OllamaChatClient(BaseAIChatClient):
    def __init__(self, host: str = None, model: str = "llama3.1", timeout: int = 180):
        self.host = host or settings.OLLAMA_HOST
        self.model = model
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return AIProvider.OLLAMA.value

    def is_available(self) -> bool:
        try:
            import requests

            response = requests.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    async def chat(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> ChatResponse:
        # Ollama doesn't support tools or thinking
        msg_list = [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": self.model,
            "messages": msg_list,
            "stream": False,
            "options": {"temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.host}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()

                message = data.get("message", {})

                return ChatResponse(
                    content=message.get("content", ""),
                    model=data.get("model", self.model),
                    provider=self.provider_name,
                    usage={},
                )
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                error_str = str(e)
                if is_recoverable_error(error_str, status_code):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable HTTP error {status_code}: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Ollama chat HTTP error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Ollama: {str(e)}",
                    provider=self.provider_name,
                )
            except Exception as e:
                error_str = str(e)
                if is_recoverable_error(error_str):
                    logger.warning(
                        f"[{self.provider_name}] Recoverable error: {error_str}"
                    )
                    raise Exception(f"Recoverable: {error_str}")
                logger.error(f"Ollama chat error: {e}")
                return ChatResponse(
                    content=f"Greška pri komunikaciji sa Ollama: {str(e)}",
                    provider=self.provider_name,
                )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        tools: Optional[List[Dict]] = None,
        thinking: bool = False,
        **kwargs,
    ) -> AsyncIterator[str]:
        msg_list = [{"role": m.role, "content": m.content} for m in messages]

        payload = {
            "model": self.model,
            "messages": msg_list,
            "stream": True,
            "options": {"temperature": 0.7},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST", f"{self.host}/api/chat", json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            delta = chunk.get("message", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            pass


# ============================================================
# UNIFIED AI SERVICE
# ============================================================


class AIChatService:
    """
    Unified AI Chat Service koji objedinjuje sve provajdere.
    """

    PROVIDER_FALLBACK_ORDER = [
        AIProvider.OPENAI,
        AIProvider.GROQ,
        AIProvider.MISTRAL,
        AIProvider.CLAUDE,
        AIProvider.DEEPSEEK,
        AIProvider.GEMINI,
        AIProvider.OLLAMA,
    ]

    def __init__(self, user_api_keys: Optional[Dict[str, str]] = None):
        """
        Inicijalizuj AI chat service.

        Args:
            user_api_keys: Opcionalni korisnički API ključevi koji override-uju sistemske
        """
        self.user_api_keys = user_api_keys or {}

        # Initialize clients
        self._clients: Dict[str, BaseAIChatClient] = {
            AIProvider.OPENAI.value: OpenAIChatClient(
                api_key=self.user_api_keys.get(AIProvider.OPENAI.value),
                model=get_valid_model("openai"),
            ),
            AIProvider.GROQ.value: OpenAIChatClient(
                api_key=self.user_api_keys.get(AIProvider.GROQ.value),
                base_url="https://api.groq.com/openai/v1",
                model=get_valid_model("groq"),
            ),
            AIProvider.MISTRAL.value: OpenAIChatClient(
                api_key=self.user_api_keys.get(AIProvider.MISTRAL.value),
                base_url="https://api.mistral.ai/v1",
                model=get_valid_model("mistral"),
            ),
            AIProvider.CLAUDE.value: ClaudeChatClient(
                api_key=self.user_api_keys.get(AIProvider.CLAUDE.value)
            ),
            AIProvider.DEEPSEEK.value: DeepSeekChatClient(
                api_key=self.user_api_keys.get(AIProvider.DEEPSEEK.value)
            ),
            AIProvider.GEMINI.value: GeminiChatClient(
                api_key=self.user_api_keys.get(AIProvider.GEMINI.value)
            ),
            AIProvider.OLLAMA.value: OllamaChatClient(),
        }

    def get_available_providers(self) -> List[ProviderInfo]:
        providers = []

        provider_configs = [
            (AIProvider.OPENAI.value, "OpenAI", get_valid_model("openai"), True, True),
            (AIProvider.GROQ.value, "Groq", get_valid_model("groq"), False, False),
            (
                AIProvider.MISTRAL.value,
                "Mistral",
                get_valid_model("mistral"),
                False,
                False,
            ),
            (
                AIProvider.CLAUDE.value,
                "Claude",
                "claude-3-5-sonnet-20241022",
                True,
                True,
            ),
            (
                AIProvider.DEEPSEEK.value,
                "DeepSeek",
                get_valid_model("deepseek"),
                True,
                True,
            ),
            (AIProvider.GEMINI.value, "Gemini", get_valid_model("gemini"), True, True),
            (
                AIProvider.OLLAMA.value,
                "Ollama (Lokalni)",
                get_valid_model("ollama"),
                False,
                False,
            ),
        ]

        for pid, name, model, supports_tools, supports_thinking in provider_configs:
            client = self._clients.get(pid)
            available = client.is_available() if client else False
            providers.append(
                ProviderInfo(
                    id=pid,
                    name=name,
                    available=available,
                    supports_tools=supports_tools,
                    supports_thinking=supports_thinking,
                    default_model=model,
                )
            )

        return providers

    def _get_client(self, provider: str) -> Optional[BaseAIChatClient]:
        if provider == AIProvider.AUTO.value:
            # Try providers in order until one works
            for p in self.PROVIDER_FALLBACK_ORDER:
                client = self._clients.get(p.value)
                if client and client.is_available():
                    return client
            return None
        return self._clients.get(provider)

    async def chat(
        self,
        messages: List[ChatMessage],
        provider: str = AIProvider.AUTO.value,
        tools: bool = True,
        thinking: bool = False,
        session: Optional[Session] = None,
        user_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Pošalji chat poruku sa automatskim fallback-om.

        Args:
            messages: Lista poruka
            provider: Provajder (auto, openai, claude, deepseek, gemini, ollama)
            tools: Da li su alati omogućeni
            thinking: Da li je thinking mode omogućen
            session: DB session za tool pozive
            user_id: User ID za perzistentne operacije

        Returns:
            ChatResponse
        """
        tool_definitions = AVAILABLE_TOOLS if tools else None

        # Determine which providers to try
        if provider == AIProvider.AUTO.value:
            providers_to_try = [p.value for p in self.PROVIDER_FALLBACK_ORDER]
        else:
            # Specific provider requested - try it first, then fall back to others
            providers_to_try = [provider]
            for p in self.PROVIDER_FALLBACK_ORDER:
                if p.value != provider:
                    providers_to_try.append(p.value)

        last_error = None

        for try_provider in providers_to_try:
            client = self._clients.get(try_provider)
            if not client or not client.is_available():
                continue

            try:
                # Make the call
                response = await client.chat(
                    messages=messages, tools=tool_definitions, thinking=thinking
                )

                # If there are tool calls, execute them
                if response.tool_calls and session:
                    tool_results = await self._execute_tools(
                        response.tool_calls, session, user_id
                    )

                    # Add tool results to messages and call again
                    messages = messages + [
                        ChatMessage(
                            role=MessageRole.ASSISTANT.value,
                            content=response.content,
                            tool_calls=[tc.__dict__ for tc in response.tool_calls],
                        )
                    ]

                    # Add tool results as user messages
                    for tr in tool_results:
                        messages.append(
                            ChatMessage(
                                role=MessageRole.TOOL.value,
                                content=tr.content,
                                tool_call_id=tr.tool_call_id,
                            )
                        )

                    # Get final response
                    response = await client.chat(
                        messages=messages, tools=tool_definitions, thinking=thinking
                    )

                # Success - return response with provider info
                return ChatResponse(
                    content=response.content,
                    tool_calls=response.tool_calls,
                    thinking=response.thinking,
                    model=getattr(response, "model", try_provider),
                    provider=try_provider,
                    usage=response.usage if hasattr(response, "usage") else {},
                )

            except Exception as e:
                logger.warning(
                    f"[{try_provider}] Greška: {str(e)}, probam sledeći provajder..."
                )
                last_error = str(e)
                continue

        # All providers failed
        return ChatResponse(
            content=f"Svi AI provajderi su neuspeli. Poslednja greška: {last_error}",
            provider=provider,
        )

    async def chat_stream(
        self,
        messages: List[ChatMessage],
        provider: str = AIProvider.AUTO.value,
        tools: bool = True,
        thinking: bool = False,
    ) -> AsyncIterator[str]:
        client = self._get_client(provider)

        if not client:
            yield "Nijedan AI provajder nije dostupan."
            return

        tool_definitions = AVAILABLE_TOOLS if tools else None

        async for chunk in client.chat_stream(
            messages=messages, tools=tool_definitions, thinking=thinking
        ):
            yield chunk

    async def _execute_tools(
        self,
        tool_calls: List[ToolCall],
        session: Session,
        user_id: Optional[str] = None,
    ) -> List[ToolResult]:
        results = []

        for tc in tool_calls:
            try:
                result_content = await self._execute_single_tool(
                    tc.name, tc.arguments, session, user_id
                )
                results.append(
                    ToolResult(
                        tool_call_id=tc.id, content=result_content, is_error=False
                    )
                )
            except Exception as e:
                results.append(
                    ToolResult(
                        tool_call_id=tc.id, content=f"Greška: {str(e)}", is_error=True
                    )
                )

        return results

    async def _execute_single_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        session: Session,
        user_id: Optional[str] = None,
    ) -> str:
        if tool_name == "search_knowledge":
            from app.services.rag import similarity_search

            query = arguments.get("query", "")
            top_k = arguments.get("top_k", 5)

            results = similarity_search(session, query, top_k=top_k)

            if not results:
                return "Nisu pronađeni rezultati u bazi znanja."

            formatted = "Pronađeni rezultati:\n\n"
            for i, r in enumerate(results[:top_k], 1):
                formatted += f"{i}. {r.get('content', '')[:300]}...\n\n"

            return formatted

        elif tool_name == "translate_text":
            from app.services.translation import TranslationService

            text = arguments.get("text", "")
            target_lang = arguments.get("target_lang", "en")
            source_lang = arguments.get("source_lang", "auto")

            service = TranslationService()
            result = service.translate(text, source_lang, target_lang)

            if result.success:
                return result.translated_text
            else:
                return f"Greška pri prevodu: {result.error}"

        elif tool_name == "generate_quiz":
            document_id = arguments.get("document_id", "")
            num_questions = arguments.get("num_questions", 5)

            return (
                f"Generisanje kviza za dokument {document_id} sa "
                f"{num_questions} pitanja. Ovo može potrajati nekoliko minuta."
            )

        elif tool_name == "get_document_summary":
            document_id = arguments.get("document_id", "")

            from app.db.models.document import Document

            doc = session.query(Document).filter(Document.id == document_id).first()

            if not doc:
                return f"Dokument {document_id} nije pronađen."

            return (
                f"Dokument: {doc.title}\nStatus: {doc.status}\n"
                f"Stranica: {doc.total_pages}\nChunks: {doc.total_chunks}"
            )

        elif tool_name == "search_documents":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)

            from app.db.models.document import Document

            docs = (
                session.query(Document)
                .filter(Document.user_id == user_id, Document.title.ilike(f"%{query}%"))
                .limit(limit)
                .all()
            )

            if not docs:
                return "Nisu pronađeni dokumenti."

            formatted = "Pronađeni dokumenti:\n"
            for d in docs:
                formatted += f"- {d.title} ({d.status})\n"

            return formatted

        else:
            return f"Nepoznat tool: {tool_name}"


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def get_ai_service(user_api_keys: Optional[Dict[str, str]] = None) -> AIChatService:
    return AIChatService(user_api_keys=user_api_keys)
