# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION CLIENT - OLLAMA
================================================================================
Klijent za Ollama API (lokalni, besplatni).

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


class OllamaClient(BaseTranslationClient):
    """Klijent za Ollama API (lokalni, besplatni)."""

    TRANSLATION_PROMPT = """You are a professional translator. Translate the following text from {source_language} to {target_language}.  # noqa: E501

Rules:
1. Maintain the original formatting and structure
2. Preserve technical terms in their original form if they are standard terminology
3. Keep any code snippets, URLs, or special markers unchanged
4. Provide only the translation, no explanations

{context}

Text to translate:
{text}

Translation:"""

    def __init__(self, host: str = None, model: str = None, timeout: int = None):
        self.host = host or settings.OLLAMA_HOST
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT
        self._available = None

    @property
    def provider_name(self) -> str:
        return TranslationProvider.OLLAMA.value

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available

        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5.0)
            self._available = response.status_code == 200
            return self._available
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
            self._available = False
            return False

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

        context_str = f"Context: {context}" if context else ""
        prompt = self.TRANSLATION_PROMPT.format(
            source_language=source_language,
            target_language=target_language,
            context=context_str,
            text=text,
        )

        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9},
                },
                timeout=self.timeout,
            )

            duration_ms = (time.time() - start_time) * 1000

            if response.status_code != 200:
                raise Exception(f"Ollama API error: {response.status_code}")

            data = response.json()
            translated_text = data.get("response", "").strip()

            prompt_eval_tokens = data.get("prompt_eval_count", 0)
            eval_tokens = data.get("eval_count", 0)
            total_tokens = prompt_eval_tokens + eval_tokens

            return TranslationResult(
                success=True,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
                provider=self.provider_name,
                tokens_used=total_tokens,
                cost=0.0,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Ollama translation failed: {e}")
            return TranslationResult(
                success=False, error=str(e), duration_ms=duration_ms
            )
