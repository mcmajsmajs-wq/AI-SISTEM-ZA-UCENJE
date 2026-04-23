# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION PROVIDER CONFIG
================================================================================
Centralna konfiguracija za sve translation provajdere.
Sadrži default modele, fallback modele i endpoint-e za validaciju.

Verzija: 1.0.0 (2026-04-23)
================================================================================
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ProviderConfig:
    """Konfiguracija za jednog provajdera."""

    name: str
    default_model: str
    fallback_models: List[str]
    test_endpoint: str
    auth_header: str  # "Bearer" za većinu, "Api-Key" za neke


PROVIDER_CONFIGS = {
    "openai": ProviderConfig(
        name="OpenAI",
        default_model="gpt-4o",
        fallback_models=["gpt-4o-mini", "gpt-3.5-turbo"],
        test_endpoint="/v1/models",
        auth_header="Bearer",
    ),
    "claude": ProviderConfig(
        name="Claude",
        default_model="claude-3-5-sonnet-20241022",
        fallback_models=["claude-3-haiku-20240307"],
        test_endpoint="/v1/messages",
        auth_header="Bearer",
    ),
    "deepseek": ProviderConfig(
        name="DeepSeek",
        default_model="deepseek-chat",
        fallback_models=["deepseek-coder"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
    "groq": ProviderConfig(
        name="Groq",
        default_model="llama-3.1-8b-instant",
        fallback_models=["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
    "mistral": ProviderConfig(
        name="Mistral",
        default_model="mistral-small-latest",
        fallback_models=["mistral-medium-latest", "mistral-large-latest"],
        test_endpoint="/v1/chat/completions",
        auth_header="Bearer",
    ),
    "ollama": ProviderConfig(
        name="Ollama",
        default_model="llama3.1",
        fallback_models=["llama3", "mistral"],
        test_endpoint="/api/tags",
        auth_header="",
    ),
    "deepl": ProviderConfig(
        name="DeepL",
        default_model="deepl",
        fallback_models=[],
        test_endpoint="/v2/translate",
        auth_header="DeepL-Auth-Key",
    ),
    "google": ProviderConfig(
        name="Google Translate",
        default_model="google-translate",
        fallback_models=[],
        test_endpoint="/language/translate/v2",
        auth_header="",
    ),
    "simplytranslate": ProviderConfig(
        name="SimplyTranslate",
        default_model="simplytranslate",
        fallback_models=[],
        test_endpoint="/translate",
        auth_header="",
    ),
}


def get_provider_config(provider: str) -> Optional[ProviderConfig]:
    """
    Vraća konfiguraciju za provajdera.

    Args:
        provider: Ime provajdera (npr. "openai", "claude")

    Returns:
        ProviderConfig ili None ako provajder ne postoji
    """
    return PROVIDER_CONFIGS.get(provider.lower())


def get_default_model(provider: str) -> str:
    """
    Vraća default model za provajdera.

    Args:
        provider: Ime provajdera

    Returns:
        Ime default modela
    """
    config = get_provider_config(provider)
    if config:
        return config.default_model
    return "gpt-4o"  # OpenAI kao fallback


def get_fallback_models(provider: str) -> List[str]:
    """
    Vraća listu fallback modela za provajdera.

    Args:
        provider: Ime provajdera

    Returns:
        Lista fallback modela
    """
    config = get_provider_config(provider)
    if config:
        return config.fallback_models
    return []
