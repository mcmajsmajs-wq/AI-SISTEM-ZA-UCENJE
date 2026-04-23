# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - GROQ
================================================================================
Klijent za Groq API (OpenAI kompatibilan).

Verzija: 1.0.0
================================================================================
"""

import logging
import time
from typing import Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.core.config import settings
from app.services.translation.clients.base import (
    BaseTranslationClient,
    TranslationResult,
)
from app.services.translation.providers import TranslationProvider
from app.utils.translation_constants import TRANSLATION_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class GroqClient(BaseTranslationClient):
    """Klijent za Groq API."""

    # Koristi shared konstantu iz translation_constants
    TRANSLATION_SYSTEM_PROMPT = TRANSLATION_SYSTEM_PROMPT

    COST_PER_1K_TOKENS = {
        "llama-3.1-8b-instant": 0.00005,
        "llama-3.1-70b-versatile": 0.00070,
        "llama-3-70b-versatile": 0.00070,
        "mixtral-8x7b-32768": 0.00024,
    }

    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or "llama-3.1-8b-instant"
        self.timeout = timeout or 60

    @property
    def provider_name(self) -> str:
        return TranslationProvider.GROQ.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _calculate_cost(self, tokens: int) -> float:
        rate = self.COST_PER_1K_TOKENS.get(self.model, 0.00005)
        return (tokens / 1000) * rate

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception),
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
    ) -> TranslationResult:
        start_time = time.time()

        if not self.api_key:
            return TranslationResult(success=False, error="Groq API key not configured")

        user_message = (
            f"Translate from {source_language} to {target_language}:\n\n{text}"
        )
        if context:
            user_message = f"Context: {context}\n\n{user_message}"

        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.TRANSLATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                    "top_p": 0.9,
                },
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"Groq API error: {response.status_code}")

            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()

            usage = data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            cost = self._calculate_cost(total_tokens)

            return TranslationResult(
                success=True,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                provider=self.provider_name,
                tokens_used=total_tokens,
                cost=cost,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Groq translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
