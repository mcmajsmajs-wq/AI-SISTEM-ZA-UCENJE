# -*- coding: utf-8 -*-
"""
===============================================================================
TRANSLATION PACKAGE - FAZA 5 Modularizacija
===============================================================================
Modularni translation service sa odvojenim klijentima.

Struktura:
├── providers.py          # TranslationProvider enum
├── service.py            # TranslationService (glavni servis)
└── clients/
    ├── __init__.py       # Client registry
    ├── base.py           # BaseTranslationClient, TranslationResult
    ├── ollama.py         # Ollama client
    ├── deepl.py          # DeepL client
    ├── openai.py         # OpenAI client
    ├── google.py         # Google Translate client
    ├── claude.py         # Claude client
    └── deepseek.py       # DeepSeek client

Verzija: 2.0.0
===============================================================================
"""

from app.core.config import settings
from app.services.translation.providers import TranslationProvider
from app.services.translation.service import (
    TranslationService,
    BatchTranslationResult,
    translation_service,
    make_gemini_client,
    make_groq_client,
    make_mistral_client,
)
from app.services.translation.clients import (
    BaseTranslationClient,
    TranslationResult,
    OllamaClient,
    DeepLClient,
    OpenAIClient,
    GoogleTranslateClient,
    ClaudeClient,
    DeepSeekClient,
    get_client,
    get_available_clients,
)

__all__ = [
    "settings",
    "TranslationProvider",
    "TranslationService",
    "BatchTranslationResult",
    "translation_service",
    "BaseTranslationClient",
    "TranslationResult",
    "OllamaClient",
    "DeepLClient",
    "OpenAIClient",
    "GoogleTranslateClient",
    "ClaudeClient",
    "DeepSeekClient",
    "get_client",
    "get_available_clients",
    "get_translation_clients",  # Alias for backward compatibility
    "make_gemini_client",
    "make_groq_client",
    "make_mistral_client",
]

# Alias for backward compatibility
get_translation_clients = get_available_clients
