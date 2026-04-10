# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - DEEPL
================================================================================
Klijent za DeepL API (online, visoki kvalitet prevoda).

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


class DeepLClient(BaseTranslationClient):
    """Klijent za DeepL API (online, visoki kvalitet prevoda)."""

    LANGUAGE_MAP = {
        "en": "EN",
        "sr": "SR",
        "de": "DE",
        "fr": "FR",
        "es": "ES",
        "it": "IT",
        "pt": "PT-PT",
        "nl": "NL",
        "pl": "PL",
        "ru": "RU",
        "ja": "JA",
        "zh": "ZH",
    }

    COST_PER_CHAR = 0.000025

    def __init__(self, api_key: str = None, use_pro: bool = None, timeout: int = None):
        self.api_key = api_key or settings.DEEPL_API_KEY
        self.use_pro = use_pro if use_pro is not None else settings.DEEPL_USE_PRO
        self.timeout = timeout or settings.DEEPL_TIMEOUT

        if self.use_pro:
            self.base_url = "https://api.deepl.com/v2"
        else:
            self.base_url = "https://api-free.deepl.com/v2"

    @property
    def provider_name(self) -> str:
        return TranslationProvider.DEEPL.value

    def is_available(self) -> bool:
        return bool(self.api_key)

    def _map_language(self, lang_code: str) -> str:
        return self.LANGUAGE_MAP.get(lang_code.lower(), lang_code.upper())

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
                success=False, error="DeepL API key not configured"
            )

        try:
            data = {
                "text": text,
                "source_lang": self._map_language(source_language),
                "target_lang": self._map_language(target_language),
            }

            if context:
                data["context"] = context

            response = httpx.post(
                f"{self.base_url}/translate",
                headers={
                    "Authorization": f"DeepL-Auth-Key {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=data,
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"DeepL API error: {response.status_code}")

            result = response.json()
            translated_text = result["translations"][0]["text"]

            char_count = len(text)
            cost = char_count * self.COST_PER_CHAR

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
            logger.error(f"DeepL translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
