# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION SERVICE
================================================================================
Servis za AI prevod teksta koristeći više provajdera:
- Ollama (lokalni, besplatni)
- DeepL (online, visoki kvalitet)
- OpenAI GPT (online)
- Google Translate (online)
- Anthropic Claude (online)

Verzija: 2.0.0
================================================================================
"""

import logging
import time
import json
from typing import List, Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.config import settings

logger = logging.getLogger(__name__)


class TranslationProvider(str, Enum):
    """Dostupni provajderi za prevod."""
    OLLAMA = "ollama"
    DEEPL = "deepl"
    OPENAI = "openai"
    GOOGLE = "google"
    CLAUDE = "claude"
    GEMINI = "gemini"
    GROQ = "groq"
    MISTRAL = "mistral"


@dataclass
class TranslationResult:
    """Rezultat prevoda."""
    success: bool
    translated_text: str = ""
    source_language: str = ""
    target_language: str = ""
    provider: str = ""
    tokens_used: int = 0
    cost: float = 0.0
    error: Optional[str] = None
    duration_ms: float = 0.0


@dataclass
class BatchTranslationResult:
    """Rezultat batch prevoda."""
    success: bool
    results: List[TranslationResult] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    total_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class BaseTranslationClient(ABC):
    """Bazna klasa za translation client-e."""
    
    @abstractmethod
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        """Prevodi tekst."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Proverava da li je provajder dostupan."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Vraća ime provajdera."""
        pass


class OllamaClient(BaseTranslationClient):
    """Klijent za Ollama API (lokalni, besplatni)."""
    
    TRANSLATION_PROMPT = """You are a professional translator. Translate the following text from {source_language} to {target_language}.

Rules:
1. Maintain the original formatting and structure
2. Preserve technical terms in their original form if they are standard terminology
3. Keep any code snippets, URLs, or special markers unchanged
4. Provide only the translation, no explanations

{context}

Text to translate:
{text}

Translation:"""

    def __init__(
        self,
        host: str = None,
        model: str = None,
        timeout: int = None
    ):
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
        retry=retry_if_exception_type(Exception)
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        start_time = time.time()
        
        context_str = f"Context: {context}" if context else ""
        prompt = self.TRANSLATION_PROMPT.format(
            source_language=source_language,
            target_language=target_language,
            context=context_str,
            text=text
        )
        
        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "top_p": 0.9}
                },
                timeout=self.timeout
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
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Ollama translation failed: {e}")
            return TranslationResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )


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
    
    def __init__(
        self,
        api_key: str = None,
        use_pro: bool = None,
        timeout: int = None
    ):
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
        retry=retry_if_exception_type(Exception)
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        start_time = time.time()
        
        if not self.api_key:
            return TranslationResult(
                success=False,
                error="DeepL API key not configured"
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
                    "Content-Type": "application/json"
                },
                json=data,
                timeout=self.timeout
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
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"DeepL translation failed: {e}")
            return TranslationResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )


class OpenAIClient(BaseTranslationClient):
    """Klijent za OpenAI GPT API."""
    
    TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the given text accurately while:
1. Maintaining the original formatting and structure
2. Preserving technical terms in their original form if they are standard terminology
3. Keeping any code snippets, URLs, or special markers unchanged
4. Providing only the translation, no explanations
5. If the input contains section markers like "### 1", "### 2" etc., preserve them exactly in the output so each translated section can be identified"""
    
    COST_PER_1K_TOKENS = {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.001,
        "gpt-4o": 0.005,
        "gpt-4o-mini": 0.00015,
    }
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        timeout: int = None
    ):
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
        retry=retry_if_exception_type(Exception)
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        start_time = time.time()
        
        if not self.api_key:
            return TranslationResult(
                success=False,
                error="OpenAI API key not configured"
            )
        
        user_message = f"Translate from {source_language} to {target_language}:\n\n{text}"
        if context:
            user_message = f"Context: {context}\n\n{user_message}"
        
        try:
            # Retry up to 3 times on 429 rate limit
            max_retries = 3
            for attempt in range(max_retries):
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": self.TRANSLATION_SYSTEM_PROMPT},
                            {"role": "user", "content": user_message}
                        ],
                        "temperature": 0.3,
                        "top_p": 0.9
                    },
                    timeout=self.timeout
                )

                if response.status_code == 429:
                    # Rate limited — respect Retry-After header or exponential backoff
                    retry_after = int(response.headers.get("Retry-After", 2 ** attempt * 5))
                    retry_after = min(retry_after, 60)  # cap at 60s
                    logger.warning(f"OpenAI rate limited (429), retrying in {retry_after}s (attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    continue

                if response.status_code != 200:
                    raise Exception(f"OpenAI API error: {response.status_code}")
                break
            else:
                raise Exception("OpenAI API error: 429 rate limit — all retries exhausted")
            
            duration_ms = (time.time() - start_time) * 1000
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
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"OpenAI translation failed: {e}")
            return TranslationResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )


class GoogleTranslateClient(BaseTranslationClient):
    """Klijent za Google Cloud Translation API."""
    
    COST_PER_1K_CHARS = 0.02
    
    def __init__(
        self,
        api_key: str = None,
        timeout: int = None
    ):
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
        retry=retry_if_exception_type(Exception)
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        start_time = time.time()
        
        if not self.api_key:
            return TranslationResult(
                success=False,
                error="Google Translate API key not configured"
            )
        
        try:
            response = httpx.post(
                f"https://translation.googleapis.com/language/translate/v2",
                params={"key": self.api_key},
                json={
                    "q": text,
                    "source": source_language,
                    "target": target_language,
                    "format": "text"
                },
                timeout=self.timeout
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
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Google Translate failed: {e}")
            return TranslationResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )


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
    
    def __init__(
        self,
        api_key: str = None,
        model: str = None,
        timeout: int = None
    ):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.CLAUDE_MODEL
        self.timeout = timeout or settings.CLAUDE_TIMEOUT
    
    @property
    def provider_name(self) -> str:
        return TranslationProvider.CLAUDE.value
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        rates = self.COST_PER_1K_TOKENS.get(self.model, {"input": 0.003, "output": 0.015})
        input_cost = (input_tokens / 1000) * rates["input"]
        output_cost = (output_tokens / 1000) * rates["output"]
        return input_cost + output_cost
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(Exception)
    )
    def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
        context: Optional[str] = None
    ) -> TranslationResult:
        start_time = time.time()
        
        if not self.api_key:
            return TranslationResult(
                success=False,
                error="Anthropic API key not configured"
            )
        
        user_message = f"Translate from {source_language} to {target_language}:\n\n{text}"
        if context:
            user_message = f"Context: {context}\n\n{user_message}"
        
        try:
            response = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": self.TRANSLATION_SYSTEM_PROMPT,
                    "messages": [
                        {"role": "user", "content": user_message}
                    ]
                },
                timeout=self.timeout
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
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"Claude translation failed: {e}")
            return TranslationResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms
            )


class OpenAICompatibleClient(BaseTranslationClient):
    """Generički klijent za OpenAI-compatible API-je (Gemini, Groq, Mistral)."""

    TRANSLATION_SYSTEM_PROMPT = """You are a professional translator. Translate the given text accurately while:
1. Maintaining the original formatting and structure
2. Preserving technical terms in their original form if they are standard terminology
3. Keeping any code snippets, URLs, or special markers unchanged
4. Providing only the translation, no explanations"""

    def __init__(self, provider_id: str, display_name: str, base_url: str,
                 api_key: str = None, model: str = None, timeout: int = 60):
        self._provider_id = provider_id
        self._display_name = display_name
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or ""
        self.model = model or ""
        self.timeout = timeout

    @property
    def provider_name(self) -> str:
        return self._display_name

    def is_available(self) -> bool:
        return bool(self.api_key)

    def translate(self, text: str, source_language: str, target_language: str,
                  context: Optional[str] = None) -> TranslationResult:
        start_time = time.time()
        if not self.api_key:
            return TranslationResult(success=False, error=f"{self._display_name} API key not configured")

        user_message = f"Translate from {source_language} to {target_language}:\n\n{text}"
        if context:
            user_message = f"Context: {context}\n\n{user_message}"

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.TRANSLATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.3,
                },
                timeout=self.timeout
            )
            duration_ms = (time.time() - start_time) * 1000
            if response.status_code != 200:
                raise Exception(f"{self._display_name} API error: {response.status_code} {response.text[:200]}")
            data = response.json()
            translated_text = data["choices"][0]["message"]["content"].strip()
            total_tokens = data.get("usage", {}).get("total_tokens", 0)
            return TranslationResult(
                success=True, translated_text=translated_text,
                source_language=source_language, target_language=target_language,
                provider=self._provider_id, tokens_used=total_tokens, duration_ms=duration_ms
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(f"{self._display_name} translation failed: {e}")
            return TranslationResult(success=False, error=str(e), duration_ms=duration_ms)


def make_gemini_client(api_key: str = None) -> OpenAICompatibleClient:
    key = api_key or getattr(settings, 'GEMINI_API_KEY', None) or ""
    return OpenAICompatibleClient(
        provider_id="gemini", display_name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key=key, model="gemini-2.0-flash"
    )


def make_groq_client(api_key: str = None) -> OpenAICompatibleClient:
    key = api_key or getattr(settings, 'GROQ_API_KEY', None) or ""
    return OpenAICompatibleClient(
        provider_id="groq", display_name="Groq",
        base_url="https://api.groq.com/openai/v1",
        api_key=key, model="llama-3.1-8b-instant"
    )


def make_mistral_client(api_key: str = None) -> OpenAICompatibleClient:
    key = api_key or getattr(settings, 'MISTRAL_API_KEY', None) or ""
    return OpenAICompatibleClient(
        provider_id="mistral", display_name="Mistral",
        base_url="https://api.mistral.ai/v1",
        api_key=key, model="mistral-small-latest"
    )


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
            TranslationProvider.GEMINI.value: make_gemini_client(),
            TranslationProvider.GROQ.value: make_groq_client(),
            TranslationProvider.MISTRAL.value: make_mistral_client(),
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
            providers.append({
                "id": provider_id,
                "name": client.provider_name,
                "available": client.is_available(),
                "type": "local" if provider_id == "ollama" else "online"
            })
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
        provider: Optional[str] = None
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
                target_language=target_language
            )
        
        if provider:
            if provider.lower() in self._clients:
                client = self._clients[provider.lower()]
                if client.is_available():
                    result = client.translate(text, source_language, target_language, context)
                    if result.success and self._glossary:
                        result.translated_text = self._apply_glossary(result.translated_text)
                    return result
            return TranslationResult(
                success=False,
                error=f"Provider '{provider}' not available"
            )
        
        clients = self._get_ordered_clients()
        
        if not clients:
            return TranslationResult(
                success=False,
                error="No translation provider available"
            )
        
        last_error = None
        for client in clients:
            logger.debug(f"Trying translation with {client.provider_name}")
            result = client.translate(text, source_language, target_language, context)
            
            if result.success:
                if self._glossary:
                    result.translated_text = self._apply_glossary(result.translated_text)
                logger.info(f"Translation successful with {client.provider_name}")
                return result
            
            last_error = result.error
            logger.warning(f"Translation failed with {client.provider_name}: {result.error}")
        
        return TranslationResult(
            success=False,
            error=f"All providers failed. Last error: {last_error}"
        )
    
    def translate_batch(
        self,
        texts: List[str],
        source_language: str = "en",
        target_language: str = "sr",
        context: Optional[str] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        provider: Optional[str] = None
    ) -> BatchTranslationResult:
        """
        Prevodi više tekstova u batch-u.
        
        Args:
            texts: Lista tekstova za prevod
            source_language: Izvorni jezik
            target_language: Ciljni jezik
            context: Dodatni kontekst
            progress_callback: Callback za praćenje progresa
            provider: Specifični provajder
            
        Returns:
            BatchTranslationResult sa svim prevodima
        """
        results = []
        total_tokens = 0
        total_cost = 0.0
        total_duration = 0.0
        errors = []
        
        for i, text in enumerate(texts):
            result = self.translate(text, source_language, target_language, context, provider)
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
            errors=errors
        )
    
    def estimate_cost(
        self,
        texts: List[str],
        provider: str = "deepl"
    ) -> Dict[str, Any]:
        """
        Estimira cenu prevoda.
        
        Args:
            texts: Lista tekstova
            provider: Provajder
            
        Returns:
            Dict sa estimacijom
        """
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
        elif provider == "claude":
            rates = ClaudeClient.COST_PER_1K_TOKENS.get(settings.CLAUDE_MODEL, {"input": 0.003, "output": 0.015})
            cost = (total_tokens / 1000) * rates["input"]
        
        return {
            "provider": provider,
            "total_texts": len(texts),
            "total_chars": total_chars,
            "total_words": total_words,
            "estimated_tokens": int(total_tokens),
            "estimated_cost": round(cost, 4)
        }


translation_service = TranslationService()
