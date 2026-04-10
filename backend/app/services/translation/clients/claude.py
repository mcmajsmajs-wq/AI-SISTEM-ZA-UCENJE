# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - CLAUDE
================================================================================
Klijent za Anthropic Claude API.

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


class ClaudeClient(BaseTranslationClient):
    """Klijent za Anthropic Claude API."""

    TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the given text accurately while:
1. Maintaining the original formatting and structure
2. Preserving technical terms in their original form if they are standard terminology
3. Keeping any code snippets, URLs, or special markers unchanged
4. Providing only the translation, no explanations"""

    COST_PER_1K_TOKENS = {
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
    }

    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.timeout = timeout or settings.CLAUDE_TIMEOUT

    @property
    def provider_name(self) -> str:
        return TranslationProvider.CLAUDE.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        rates = self.COST_PER_1K_TOKENS.get(
            self.model, {"input": 0.003, "output": 0.015}
        )
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        return input_cost + output_cost

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
                success=False, error="Anthropic API key not configured"
            )

        user_message = (
            f"Translate from {source_language} to {target_language}:\n\n{text}"
        )
        if context:
            user_message = f"Context: {context}\n\n{user_message}"

        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": self.TRANSLATION_SYSTEM_PROMPT,
                    "messages": [{"role": "user", "content": user_message}],
                },
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"Claude API error: {response.status_code}")

            data = response.json()
            translated_text = data["content"][0]["text"].strip()

            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

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
            logger.error(f"Claude translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )