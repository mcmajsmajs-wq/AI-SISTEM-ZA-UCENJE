# -*- coding: utf-8 -*-
"""
===============================================================================
TRANSLATION CLIENTS - EXPORTS
===============================================================================
Svi translation client-i.

Verzija: 2.0.0 (FAZA 5 - Modularizacija)
===============================================================================
"""

from app.core.config import settings
from app.services.translation.clients.base import (
    BaseTranslationClient,
    TranslationResult,
)
from app.services.translation.clients.ollama import OllamaClient
from app.services.translation.clients.deepl import DeepLClient
from app.services.translation.clients.openai import OpenAIClient
from app.services.translation.clients.google import GoogleTranslateClient
from app.services.translation.clients.claude import ClaudeClient
from app.services.translation.clients.deepseek import DeepSeekClient
from app.services.translation.clients.groq import GroqClient
from app.services.translation.clients.mistral import MistralClient
from app.services.translation.clients.simplytranslate import SimplyTranslateClient
from app.services.translation.providers import TranslationProvider


def get_client(provider: str, **kwargs):
    """
    Kreira translation client za zadati provider.

    Args:
        provider: Ime provider-a (ollama, deepl, openai, google, claude, deepseek)
        **kwargs: Dodatni parametri za client (api_key, model, etc.)

    Returns:
        BaseTranslationClient instanca ili None ako provider nije podržan
    """
    provider = provider.lower()

    clients = {
        "ollama": OllamaClient,
        "deepl": DeepLClient,
        "openai": OpenAIClient,
        "google": GoogleTranslateClient,
        "google-translate": GoogleTranslateClient,
        "claude": ClaudeClient,
        "anthropic": ClaudeClient,
        "deepseek": DeepSeekClient,
        "groq": GroqClient,
        "mistral": MistralClient,
        "simplytranslate": SimplyTranslateClient,
    }

    client_class = clients.get(provider)
    if client_class:
        return client_class(**kwargs)
    return None


def get_available_clients():
    """
    Vraća listu dostupnih translation client-a.

    Returns:
        List[dict] - Lista sa info o dostupnim client-ima
    """
    available = []
    for provider in [
        "ollama",
        "deepl",
        "openai",
        "google",
        "claude",
        "deepseek",
        "simplytranslate",
    ]:
        client = get_client(provider)
        if client and client.is_available():
            available.append(
                {
                    "provider": provider,
                    "name": client.provider_name,
                    "available": True,
                }
            )
    return available


__all__ = [
    "settings",
    "BaseTranslationClient",
    "TranslationResult",
    "OllamaClient",
    "DeepLClient",
    "OpenAIClient",
    "GoogleTranslateClient",
    "ClaudeClient",
    "DeepSeekClient",
    "GroqClient",
    "MistralClient",
    "SimplyTranslateClient",
    "TranslationProvider",
    "get_client",
    "get_available_clients",
]
