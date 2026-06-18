# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION VALIDATOR
================================================================================
Validacija API ključeva i modela za translation servise.
Vraća jasne poruke za korisnika.

Verzija: 1.0.0 (2026-04-23)
================================================================================
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

import httpx

from app.services.translation.translation_config import (
    get_provider_config,
    get_fallback_models,
)

logger = logging.getLogger(__name__)


class ValidationStatus(str, Enum):
    """Status validacije."""

    OK = "ok"
    ERROR = "error"
    API_KEY_INVALID = "api_key_invalid"
    MODEL_INVALID = "model_invalid"
    MODEL_DEPRECATED = "model_deprecated"


@dataclass
class ValidationResult:
    """Rezultat validacije sa porukama za korisnika."""

    status: ValidationStatus
    provider: str
    api_key_valid: bool
    model_valid: bool
    model_used: str
    available_models: List[str]
    user_message: str  # Poruka za korisnika
    details: str  # Tehnički detalji

    @property
    def is_ok(self) -> bool:
        """Da li je validacija prošla."""
        return self.status in [ValidationStatus.OK, ValidationStatus.MODEL_DEPRECATED]


class TranslationValidator:
    """Validacija API ključeva i modela za translation."""

    # Keš za validaciju (u produkciji bi bilo u Redis)
    _validation_cache = {}

    @classmethod
    def validate_provider(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> ValidationResult:
        """
        Validira provider - API key i model.

        Args:
            provider: Ime providera (openai, claude, etc.)
            api_key: API ključ (opciono, koristi settings ako nije prosleđen)
            model: Model koji korisnik želi (opciono)

        Returns:
            ValidationResult sa statusom i porukom za korisnika
        """
        config = get_provider_config(provider)
        if not config:
            return ValidationResult(
                status=ValidationStatus.ERROR,
                provider=provider,
                api_key_valid=False,
                model_valid=False,
                model_used="",
                available_models=[],
                user_message=f"Nepoznat provider: {provider}",
                details=f"Provider '{provider}' nije pronađen u konfiguraciji",
            )

        # Ako korisnik nije dao model, koristi default
        if not model:
            model = config.default_model

        # Testiraj API ključ
        api_key_valid, key_message = cls._validate_api_key(provider, api_key, config)

        if not api_key_valid:
            return ValidationResult(
                status=ValidationStatus.API_KEY_INVALID,
                provider=provider,
                api_key_valid=False,
                model_valid=False,
                model_used=model,
                available_models=[],
                user_message=key_message,  # Jasna poruka za korisnika!
                details=f"API ključ za {provider} nije validan",
            )

        # Testiraj model (samo za LLM provajdere)
        model_valid, model_used, model_message = cls._validate_model(
            provider, model, config
        )

        if model_valid:
            return ValidationResult(
                status=ValidationStatus.OK,
                provider=provider,
                api_key_valid=True,
                model_valid=True,
                model_used=model_used,
                available_models=[],
                user_message=f"✅ {config.name}: API ključ i model su validni",
                details=f"Using model: {model_used}",
            )
        elif model == model_used:
            # Model invalid ali je fallback na default
            return ValidationResult(
                status=ValidationStatus.MODEL_DEPRECATED,
                provider=provider,
                api_key_valid=True,
                model_valid=True,
                model_used=model_used,
                available_models=get_fallback_models(provider),
                user_message=model_message,
                details=f"Model {model} deprecated, using: {model_used}",
            )
        else:
            return ValidationResult(
                status=ValidationStatus.MODEL_INVALID,
                provider=provider,
                api_key_valid=True,
                model_valid=False,
                model_used=model_used,
                available_models=get_fallback_models(provider),
                user_message=model_message,
                details=f"Model {model} not available",
            )

    @classmethod
    def _validate_api_key(cls, provider: str, api_key: Optional[str], config) -> tuple:
        """
        Validira API ključ - pravi test request.

        Returns:
            (is_valid, user_message)
        """
        if not api_key:
            return (
                False,
                f"❌ {config.name}: API ključ nije podešen. Molim dodajte API ključ u podešavanja.",
            )

        try:
            if provider == "openai":
                response = httpx.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=10,
                )
            elif provider == "claude":
                response = httpx.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                    timeout=10,
                )
            elif provider == "deepseek":
                response = httpx.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                    timeout=10,
                )
            elif provider == "groq":
                response = httpx.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                    timeout=10,
                )
            elif provider == "mistral":
                response = httpx.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "mistral-small-latest",
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                    timeout=10,
                )
            else:
                # Za ostale (deepl, google, simplytranslate, ollama) - ne testiramo detaljno
                return True, ""

            if response.status_code == 200:
                return True, ""
            elif response.status_code == 401:
                return (
                    False,
                    f"❌ {config.name}: API ključ je istekao ili nije validan. Molim ažurirajte API ključ.",
                )
            elif response.status_code == 403:
                return (
                    False,
                    f"❌ {config.name}: Pristup odbijen. Proverite da li je API ključ ispravan.",
                )
            elif response.status_code == 429:
                return (
                    False,
                    f"⚠️ {config.name}: Prekoračen limit. Sačekajte malo pa pokušajte ponovo.",
                )
            else:
                return (
                    False,
                    f"❌ {config.name}: Greška pri validaciji ({response.status_code})",
                )

        except httpx.TimeoutException:
            return False, f"⚠️ {config.name}: Timeout. Proverite internet konekciju."
        except Exception as e:
            logger.warning(f"API key validation error for {provider}: {e}")
            return True, ""  # Ako ne možemo da testiramo, pretpostavljamo da je OK

    @classmethod
    def _validate_model(cls, provider: str, model: str, config) -> tuple:
        """
        Validira model - proverava da li postoji.

        Returns:
            (is_valid, model_used, user_message)
        """
        # Za REST provajdere (deepl, google, simplytranslate) - nema modela
        if provider in ["deepl", "google", "simplytranslate", "ollama"]:
            return True, model, ""

        # Za LLM provajdere - proveri model
        # Ako korisnik koristi default model, uvek je OK
        if model == config.default_model:
            return True, model, ""

        # Proveri da li je model u fallback listi
        fallback_models = config.fallback_models or []
        if model in fallback_models:
            return True, model, ""

        # Model nije prepoznat - koristi default
        return (
            False,
            config.default_model,
            f"⚠️ {config.name}: Model '{model}' nije dostupan. Koristim '{config.default_model}' umesto toga.",
        )


def validate_translation_provider(
    provider: str, api_key: Optional[str] = None, model: Optional[str] = None
) -> ValidationResult:
    """
    Glavna funkcija za validaciju translation providera.
    Koristi se pre translate() da se osigura da sve radi.

    Args:
        provider: Ime providera
        api_key: API ključ
        model: Model

    Returns:
        ValidationResult sa porukom za korisnika
    """
    return TranslationValidator.validate_provider(provider, api_key, model)
