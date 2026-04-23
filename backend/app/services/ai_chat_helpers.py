# -*- coding: utf-8 -*-
"""
================================================================================
AI CHAT HELPERS
================================================================================
Pomoćne funkcije i konstante za AI Chat service.

Verzija: 1.0.0 (2026-04-23)
================================================================================
"""

from enum import Enum
from typing import Optional


# Valid modeli po provideru
VALID_MODELS = {
    "openai": "gpt-4o",
    "groq": "llama-3.3-70b-versatile",
    "mistral": "mistral-small-latest",
    "deepseek": "deepseek-chat",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.1",
}


def get_valid_model(provider: str, fallback: str = None) -> str:
    """
    Vrati validan model za provider.

    Args:
        provider: Ime providera
        fallback: Fallback model ako nije pronađen

    Returns:
        Validno ime modela
    """
    return VALID_MODELS.get(provider, fallback or "gpt-4o")


# Recoverable error kodovi
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
    """
    Proveri da li je greška recoveriable.

    Args:
        error: Poruka greške
        status_code: HTTP status code

    Returns:
        True ako je recoverable
    """
    if status_code and status_code in [401, 402, 403, 429]:
        return True
    error_lower = error.lower()
    return any(x in error_lower for x in RECOVERABLE_ERRORS)


class AIProvider(str, Enum):
    """AI Provider enum."""

    AUTO = "auto"
    OPENAI = "openai"
    GROQ = "groq"
    DEEPSEEK = "deepseek"
    MISTRAL = "mistral"
    GEMINI = "gemini"
    OLLAMA = "ollama"
    CLAUDE = "claude"


class MessageRole(str, Enum):
    """Message role enum."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
