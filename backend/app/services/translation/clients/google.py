# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - GOOGLE
================================================================================
Klijent za Google Cloud Translation API.

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


class GoogleTranslateClient(BaseTranslationClient):
    """Klijent za Google Cloud Translation API."""

    COST_PER_1K_CHARS = 0.02

    def __init__(self, api_key: str = None, timeout: int = None):
        self.api_key = api_key or settings.GOOGLE_TRANSLATE_API_KEY
        self.timeout = timeout or settings.GOOGLE_TRANSLATE_TIMEOUT
        self.base_url = "https://translation.googleapis.com/v3"

    @property
    def provider_name(self) -> str:
        return TranslationProvider.GOOGLE.value

    def is_available(self) -> bool:
        return bool(self.api_key)

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
                success=False, error="Google Translate API key not configured"
            )

        try:
            response = httpx.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": self.api_key},
                json={
                    "q": text,
                    "source": source_language,
                    "target": target_language,
                    "format": "text",
                },
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"Google Translate API error: {response.status_code}")

            result = response.json()
            translated_text = result["data"]["translations"][0]["translatedText"]

            char_count = len(text)
            cost = (char_count / 1000) * self.COST_PER_1K_CHARS

            return TranslationResult(
                success=True,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                provider=self.provider_name,
                tokens_used=char_count,
                cost=cost,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Google Translate failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
