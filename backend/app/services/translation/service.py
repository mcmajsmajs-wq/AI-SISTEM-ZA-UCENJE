# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION SERVICE
================================================================================
Glavni servis za prevod teksta sa više provajdera i fallback mehanizmom.

Verzija: 2.0.0 (FAZA 5 - Modularizacija)
================================================================================
"""

import logging
from typing import List, Optional, Dict, Any, Callable

from app.core.config import settings
from app.services.translation.clients import (
    BaseTranslationClient,
    TranslationResult,
    OllamaClient,
    DeepLClient,
    OpenAIClient,
    GoogleTranslateClient,
    ClaudeClient,
    DeepSeekClient,
    GroqClient,
    MistralClient,
)
from app.services.translation.providers import TranslationProvider
from app.services.translation.translation_validator import (
    validate_translation_provider,
    ValidationStatus,
)
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class BatchTranslationResult:
    """Rezultat batch prevoda."""

    success: bool
    results: List[TranslationResult] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    total_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class TranslationService:
    """
    ================================================================================
    TRANSLATION SERVICE
    ================================================================================
    Glavni servis za prevod teksta sa više provajdera i fallback mehanizmom.
    Podržava: Ollama (lokalni), DeepL, OpenAI, Google Translate, Claude
    ================================================================================
    """

    LANGUAGE_NAMES = {
        "en": "English",
        "sr": "Serbian",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "nl": "Dutch",
        "pl": "Polish",
    }

    def __init__(self, fallback_order: str = None):
        """
        Inicijalizuje Translation Service.

        Args:
            fallback_order: Redosled provajdera (npr. "ollama,deepl,openai,google,claude")
        """
        self.fallback_order = fallback_order or settings.TRANSLATION_FALLBACK_ORDER
        self.prefer_local = settings.TRANSLATION_PREFER_LOCAL

        self._clients: Dict[str, BaseTranslationClient] = {
            TranslationProvider.OLLAMA.value: OllamaClient(),
            TranslationProvider.DEEPL.value: DeepLClient(),
            TranslationProvider.OPENAI.value: OpenAIClient(),
            TranslationProvider.GOOGLE.value: GoogleTranslateClient(),
            TranslationProvider.CLAUDE.value: ClaudeClient(),
            TranslationProvider.DEEPSEEK.value: DeepSeekClient(),
            TranslationProvider.GROQ.value: GroqClient(),
            TranslationProvider.MISTRAL.value: MistralClient(),
        }

        self._glossary: Dict[str, str] = {}

    def get_language_name(self, code: str) -> str:
        return self.LANGUAGE_NAMES.get(code, code)

    def set_glossary(self, glossary: Dict[str, str]) -> None:
        self._glossary = glossary

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Vraća listu dostupnih provajdera."""
        providers = []
        for provider_id, client in self._clients.items():
            providers.append(
                {
                    "id": provider_id,
                    "name": client.provider_name,
                    "available": client.is_available(),
                    "type": "local" if provider_id == "ollama" else "online",
                }
            )
        return providers

    def _get_ordered_clients(self) -> List[BaseTranslationClient]:
        """Vraća klijente u redosledu fallback-a."""
        order = [p.strip().lower() for p in self.fallback_order.split(",")]
        clients = []

        for provider in order:
            if provider in self._clients:
                client = self._clients[provider]
                if client.is_available():
                    clients.append(client)

        for provider, client in self._clients.items():
            if client not in clients and client.is_available():
                clients.append(client)

        return clients

    def _apply_glossary(self, text: str) -> str:
        for term, translation in self._glossary.items():
            text = text.replace(term, translation)
        return text

    def translate(
        self,
        text: str,
        source_language: str = "en",
        target_language: str = "sr",
        context: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> TranslationResult:
        """
        Prevodi tekst.

        Args:
            text: Tekst za prevod
            source_language: Izvorni jezik (default: en)
            target_language: Ciljni jezik (default: sr)
            context: Dodatni kontekst
            provider: Specifični provajder (opciono)

        Returns:
            TranslationResult sa prevodom
        """
        if not text or not text.strip():
            return TranslationResult(
                success=True,
                translated_text="",
                source_language=source_language,
                target_language=target_language,
            )

        # Ako je specificiran provider, validiraj ga PRVI
        if provider:
            if provider.lower() in self._clients:
                client = self._clients[provider.lower()]

                # Validacija: proveri API key i model
                validation = validate_translation_provider(
                    provider=provider.lower(),
                    api_key=client.api_key if hasattr(client, "api_key") else None,
                    model=client.model if hasattr(client, "model") else None,
                )

                if not validation.is_ok:
                    # VRATI JASNU PORUKU KORISNIKU!
                    return TranslationResult(
                        success=False,
                        error=validation.user_message,
                        source_language=source_language,
                        target_language=target_language,
                    )

                # Ako je model deprecated ali radi sa fallback
                if validation.status == ValidationStatus.MODEL_DEPRECATED:
                    logger.info(validation.user_message)

        if provider:
            if provider.lower() in self._clients:
                client = self._clients[provider.lower()]
                if client.is_available():
                    result = client.translate(
                        text, source_language, target_language, context
                    )
                    if result.success and self._glossary:
                        result.translated_text = self._apply_glossary(
                            result.translated_text
                        )
                    return result
            return TranslationResult(
                success=False, error=f"Provider '{provider}' not available"
            )

        clients = self._get_ordered_clients()

        if not clients:
            return TranslationResult(
                success=False, error="No translation provider available"
            )

        last_error = None
        for client in clients:
            logger.debug(f"Trying translation with {client.provider_name}")
            result = client.translate(text, source_language, target_language, context)

            if result.success:
                if self._glossary:
                    result.translated_text = self._apply_glossary(
                        result.translated_text
                    )
                logger.info(f"Translation successful with {client.provider_name}")
                return result

            last_error = result.error
            logger.warning(
                f"Translation failed with {client.provider_name}: {result.error}"
            )

        return TranslationResult(
            success=False, error=f"All providers failed. Last error: {last_error}"
        )

    def translate_batch(
        self,
        texts: List[str],
        source_language: str = "en",
        target_language: str = "sr",
        context: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        provider: Optional[str] = None,
    ) -> BatchTranslationResult:
        """
        Prevodi više tekstova u batch-u.
        """
        results = []
        total_tokens = 0
        total_cost = 0.0
        total_duration = 0.0
        errors = []

        for i, text in enumerate(texts):
            result = self.translate(
                text, source_language, target_language, context, provider
            )
            results.append(result)

            if result.success:
                total_tokens += result.tokens_used
                total_cost += result.cost
            else:
                errors.append(f"Text {i}: {result.error}")

            total_duration += result.duration_ms

            if progress_callback:
                progress_callback(i + 1, len(texts))

        return BatchTranslationResult(
            success=len(errors) == 0,
            results=results,
            total_tokens=total_tokens,
            total_cost=total_cost,
            total_duration_ms=total_duration,
            errors=errors,
        )

    def estimate_cost(
        self, texts: List[str], provider: str = "deepl"
    ) -> Dict[str, Any]:
        """Estimira cenu prevoda."""
        try:
            import tiktoken

            encoder = tiktoken.get_encoding("cl100k_base")
        except ImportError:
            encoder = None

        total_chars = sum(len(t) for t in texts)
        total_words = sum(len(t.split()) for t in texts)

        if encoder:
            total_tokens = sum(len(encoder.encode(t)) for t in texts)
        else:
            total_tokens = int(total_words * 1.3)

        provider = provider.lower()
        cost = 0.0

        if provider == "ollama":
            cost = 0.0
        elif provider == "deepl":
            cost = (total_chars / 1000) * DeepLClient.COST_PER_CHAR
        elif provider == "google":
            cost = (total_chars / 1000) * GoogleTranslateClient.COST_PER_1K_CHARS
        elif provider == "openai":
            rate = OpenAIClient.COST_PER_1K_TOKENS.get(settings.OPENAI_MODEL, 0.03)
            cost = (total_tokens / 1000) * rate

        return {
            "provider": provider,
            "total_texts": len(texts),
            "total_chars": total_chars,
            "total_words": total_words,
            "estimated_tokens": int(total_tokens),
            "estimated_cost": round(cost, 4),
        }


translation_service = TranslationService()


def make_gemini_client(api_key: str):
    """Kreira Gemini translation client za direktan poziv."""

    class GeminiTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(
                text, source, target, provider="gemini"
            )

    return GeminiTranslationClient(api_key)


def make_groq_client(api_key: str):
    """Kreira Groq translation client (koristi OpenAI kompatibilan API)."""

    class GroqTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(text, source, target, provider="groq")

    return GroqTranslationClient(api_key)


def make_mistral_client(api_key: str):
    """Kreira Mistral translation client za direktan poziv."""

    class MistralTranslationClient:
        def __init__(self, key):
            self.key = key

        def translate(self, text, source, target):
            return translation_service.translate(
                text, source, target, provider="mistral"
            )

    return MistralTranslationClient(api_key)
