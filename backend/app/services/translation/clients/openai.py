# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - OPENAI
================================================================================
Klijent za OpenAI GPT API.

Verzija: 2.0.0 (FAZA 5 - Modularizacija)
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

logger = logging.getLogger(__name__)


class OpenAIClient(BaseTranslationClient):
    """Klijent za OpenAI GPT API."""

    TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the given text accurately while:
1. Maintaining the original formatting and structure
2. Preserving technical terms in their original form if they are standard terminology
3. Keeping any code snippets, URLs, or special markers unchanged
4. Providing only the translation, no explanations"""

    COST_PER_1K_TOKENS = {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.001,
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
    }

    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.timeout = timeout or settings.OPENAI_TIMEOUT

    @property
    def provider_name(self) -> str:
        return TranslationProvider.OPENAI.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _calculate_cost(self, tokens: int) -> float:
        rate = self.COST_PER_1K_TOKENS.get(self.model, 0.03)
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
            return TranslationResult(
                success=False, error="OpenAI API key not configured"
            )

        user_message = (
            f"Translate from {source_language} to {target_language}:\n\n{text}"
        )
        if context:
            user_message = f"Context: {context}\n\n{user_message}"

        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
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
                raise Exception(f"OpenAI API error: {response.status_code}")

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
            logger.error(f"OpenAI translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
