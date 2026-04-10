# -*- coding: utf-8 -*-
"""
===============================================================================
TRANSLATION SERVICE - BACKWARD COMPATIBILITY LAYER
===============================================================================
This file now re-exports from the new modular translation service.
For new code, use: from app.services.translation import TranslationService

Verzija: 2.0.1 (FAZA 5 - Modularizacija - Backward Compatible)
===============================================================================
"""

import logging

from app.core.config import settings
from app.services.translation import (
    TranslationProvider,
    TranslationService as _TranslationService,
    BatchTranslationResult,
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

logger = logging.getLogger(__name__)


class TranslationService(_TranslationService):
    """
    TranslationService backward compatibility wrapper.
    Deprecated: Use from app.services.translation import TranslationService
    """

    pass


translation_service = TranslationService()


def make_gemini_client(api_key: str):
    """
    Kreira Gemini translation client za direktan poziv.

    Args:
        api_key: Gemini API ključ

    Returns:
        GeminiTranslationClient instanca sa translate metodom
    """

    class GeminiTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(
                text, source, target, provider="gemini"
            )

    return GeminiTranslationClient(api_key)


def make_groq_client(api_key: str):
    """
    Kreira Groq translation client (koristi OpenAI kompatibilan API).

    Args:
        api_key: Groq API ključ

    Returns:
        GroqTranslationClient instanca sa translate metodom
    """

    class GroqTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(text, source, target, provider="groq")

    return GroqTranslationClient(api_key)


def make_mistral_client(api_key: str):
    """
    Kreira Mistral translation client za direktan poziv.

    Args:
        api_key: Mistral API ključ

    Returns:
        MistralTranslationClient instanca sa translate metodom
    """

    class MistralTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(
                text, source, target, provider="mistral"
            )

    return MistralTranslationClient(api_key)


__all__ = [
    "settings",
    "TranslationProvider",
    "TranslationResult",
    "BatchTranslationResult",
    "BaseTranslationClient",
    "OllamaClient",
    "DeepLClient",
    "OpenAIClient",
    "GoogleTranslateClient",
    "ClaudeClient",
    "DeepSeekClient",
    "TranslationService",
    "translation_service",
    "get_client",
    "get_available_clients",
    "make_gemini_client",
    "make_groq_client",
    "make_mistral_client",
]
