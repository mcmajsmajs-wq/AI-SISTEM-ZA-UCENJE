# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - SIMPLYTRANSLATE
================================================================================
Klijent za SimplyTranslate API (besplatan, bez registracije).

Verzija: 1.0.0
================================================================================

Limit (besplatno):
- 100 requesta dnevno
- 500 karaktera po requestu
- 1 concurrent request

Link: https://simplytranslate.ai/
"""

import logging
import time
from typing import Optional

import httpx

from app.services.translation.clients.base import (
    BaseTranslationClient,
    TranslationResult,
)
from app.services.translation.providers import TranslationProvider

logger = logging.getLogger(__name__)


class SimplyTranslateClient(BaseTranslationClient):
    """Klijent za SimplyTranslate API (besplatan, bez registracije)."""

    BASE_URL = "https://api.simplytranslate.ai"
    COST_PER_CHAR = 0.0

    LANGUAGE_MAP = {
        "en": "english",
        "sr": "serbian",
        "de": "german",
        "fr": "french",
        "es": "spanish",
        "it": "italian",
        "pt": "portuguese",
        "ru": "russian",
        "ja": "japanese",
        "zh": "chinese",
        "ko": "korean",
        "ar": "arabic",
        "hi": "hindi",
        "tr": "turkish",
        "nl": "dutch",
        "pl": "polish",
        "sv": "swedish",
        "da": "danish",
        "no": "norwegian",
        "fi": "finnish",
        "el": "greek",
        "he": "hebrew",
        "th": "thai",
        "vi": "vietnamese",
        "id": "indonesian",
        "ms": "malay",
        "ro": "romanian",
        "hu": "hungarian",
        "cs": "czech",
        "sk": "slovak",
        "uk": "ukrainian",
        "bg": "bulgarian",
        "hr": "croatian",
        "sl": "slovenian",
        "lt": "lithuanian",
        "lv": "latvian",
        "et": "estonian",
    }

    def __init__(self, api_key: str = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return TranslationProvider.SIMPLYTRANSLATE.value

    def is_available(self) -> bool:
        return True

    def _map_language(self, lang_code: str) -> str:
        lang = lang_code.lower()
        if lang in ["sr", "sr-cyrl"]:
            return "serbian"
        return self.LANGUAGE_MAP.get(lang, lang_code)

    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None,
    ) -> TranslationResult:
        start_time = time.time()

        if len(text) > 500:
            return TranslationResult(
                success=False,
                error="Text too long (max 500 characters for SimplyTranslate)",
            )

        try:
            headers = {
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["X-API-Key"] = self.api_key

            response = httpx.post(
                f"{self.BASE_URL}/translate",
                headers=headers,
                json={
                    "text": text,
                    "from": self._map_language(source_language),
                    "to": self._map_language(target_language),
                },
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                error_msg = response.json().get("error", f"HTTP {response.status_code}")
                raise Exception(f"SimplyTranslate API error: {error_msg}")

            result = response.json()
            translated_text = result.get("result", "")

            char_count = len(text)

            return TranslationResult(
                success=True,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                provider=self.provider_name,
                tokens_used=char_count,
                cost=0.0,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"SimplyTranslate translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
