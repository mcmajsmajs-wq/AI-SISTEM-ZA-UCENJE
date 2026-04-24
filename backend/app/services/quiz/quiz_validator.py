# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ VALIDATOR - Validator for Quiz AI Providers
================================================================================

Proverava da li su quiz AI provideri dostupni sa validnim API ključevima i modelima.

Verzija: 1.0.0
================================================================================
"""

import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from app.services.quiz.clients import _build_clients, _PROVIDER_ORDER
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class QuizValidationResult:
    """Rezultat validacije quiz providera."""

    provider: str
    is_ok: bool
    status: str  # "ok", "error", "warning"
    user_message: str
    model: Optional[str] = None
    error: Optional[str] = None


def _get_quiz_provider_keys(provider: str) -> tuple:
    """
    Dohvata API ključeve za specificiran quiz provider.

    Args:
        provider: Ime providera

    Returns:
        tuple: (api_key, model_name)
    """
    # Map provider -> settings attribute
    key_attr = {
        "groq": "SYSTEM_GROQ_API_KEY",
        "openai": "SYSTEM_OPENAI_API_KEY",
        "claude": "SYSTEM_CLAUDE_API_KEY",
        "gemini": "SYSTEM_GEMINI_API_KEY",
        "mistral": "SYSTEM_MISTRAL_API_KEY",
        "deepseek": "SYSTEM_DEEPSEEK_API_KEY",
        "ollama": None,  # Local, no API key needed
    }.get(provider)

    model_attr = {
        "groq": "QUIZ_GROQ_MODEL",
        "openai": "QUIZ_OPENAI_MODEL",
        "claude": "QUIZ_CLAUDE_MODEL",
        "gemini": "GEMINI_MODEL",
        "mistral": "MISTRAL_MODEL",
        "deepseek": "DEEPSEEK_MODEL",
        "ollama": "OLLAMA_MODEL",
    }.get(provider)

    api_key = getattr(settings, key_attr, None) if key_attr else None
    model = getattr(settings, model_attr, None) if model_attr else None

    return api_key, model


def validate_quiz_provider(
    provider: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    test_generate: bool = False,
) -> QuizValidationResult:
    """
    Validira single quiz provider.

    Args:
        provider: Ime providera
        api_key: Opcioni override za API ključ
        model: Opcioni override za model
        test_generate: Da li se radi test generacija (skuplje)

    Returns:
        QuizValidationResult: Rezultat validacije
    """
    try:
        # Get keys from settings if not provided
        if api_key is None:
            api_key, model = _get_quiz_provider_keys(provider)

        # Special case: Ollama - always available if configured
        if provider == "ollama" or provider == "openai_compat":
            return QuizValidationResult(
                provider=provider,
                is_ok=True,
                status="ok",
                user_message="Provajder je dostupan",
                model=model or "local",
            )

        # No API key - fail
        if not api_key:
            return QuizValidationResult(
                provider=provider,
                is_ok=False,
                status="error",
                user_message=f"API ključ za {provider} nije podešen. Molimo vas da ga dodate u podešavanjima.",
                model=model,
                error="API key not configured",
            )

        # Build client and check availability
        clients = _build_clients(**{f"user_{provider}_key": api_key})
        client = clients.get(provider)

        if not client:
            return QuizValidationResult(
                provider=provider,
                is_ok=False,
                status="error",
                user_message=f"Provider {provider} nije podržan.",
                model=model,
                error="Provider not available",
            )

        # Check availability
        if not client.is_available():
            return QuizValidationResult(
                provider=provider,
                is_ok=False,
                status="error",
                user_message=f"API ključ za {provider} je nevažeći ili je istekao. Molimo vas da osvežite ključ u podešavanjima.",
                model=model,
                error="API key invalid or expired",
            )

        # Optional: test generate
        if test_generate:
            test_text = "Ovo je test tekst od 50 reči koje služe kao primer za generisanje simplest mogućeg kviz pitanja."
            success, raw, error = client.generate(test_text, 1)

            if not success:
                return QuizValidationResult(
                    provider=provider,
                    is_ok=False,
                    status="error",
                    user_message=f"Greška pri testiranju {provider}: {error}",
                    model=model,
                    error=error,
                )

        return QuizValidationResult(
            provider=provider,
            is_ok=True,
            status="ok",
            user_message="Provajder je dostupan",
            model=model,
        )

    except Exception as e:
        logger.error(f"Greška pri validaciji {provider}: {e}")
        return QuizValidationResult(
            provider=provider,
            is_ok=False,
            status="error",
            user_message=f"Došlo je do greške pri validaciji: {str(e)}",
            model=model,
            error=str(e),
        )


def validate_all_quiz_providers() -> List[QuizValidationResult]:
    """
    Validira sve quiz provajdere.

    Returns:
        List[QuizValidationResult]: Lista rezultata za sve provajdere
    """
    results = []
    for provider in _PROVIDER_ORDER:
        result = validate_quiz_provider(provider)
        results.append(result)
    return results
