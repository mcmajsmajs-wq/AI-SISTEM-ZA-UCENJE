# -*- coding: utf-8 -*-
"""
================================================================================
API KEY VALIDATORS
================================================================================
FAZA 8: Validacija API ključeva za različite provajdere.

Validira format API ključeva za podržane AI provajdere:
- OpenAI
- Anthropic (Claude)
- Google (Gemini)
- Ollama
- Groq
- Mistral
- DeepSeek

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-09
================================================================================
"""

import re
from typing import Dict, List, Optional, Tuple


class APIKeyValidator:
    """Validacija API ključeva za AI provajdere.

    Pruža validaciju formata i strukture API ključeva za različite
    provajdere bez čuvanja samih ključeva.
    """

    PROVIDER_PATTERNS: Dict[str, str] = {
        "openai": r"^sk-[A-Za-z0-9_-]{20,}$",
        "claude": r"^sk-ant-[a-zA-Z0-9_-]{20,}$",
        "gemini": r"^[A-Za-z0-9_-]{20,}$",
        "ollama": r"^.*$",  # Accept any - Ollama might not need key
        "groq": r"^gsk_[A-Za-z0-9_-]{20,}$",
        "mistral": r"^[A-Za-z0-9_-]{20,}$",
        "deepseek": r"^sk-[A-Za-z0-9_-]{20,}$",
    }

    PROVIDER_SCOPES: Dict[str, List[str]] = {
        "openai": ["gpt-4", "gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "claude": ["claude-sonnet-4", "claude-3-opus", "claude-3-sonnet"],
        "gemini": ["gemini-2.0-flash", "gemini-pro", "gemini-1.5-pro"],
        "ollama": ["llama3.1", "mistral", "codellama"],
        "groq": ["llama-3.1-70b", "mixtral-8x7b", "llama3-70b"],
        "mistral": ["mistral-large", "mistral-small", "codestral"],
        "deepseek": ["deepseek-chat", "deepseek-coder"],
    }

    @classmethod
    def validate(cls, provider: str, api_key: str) -> Tuple[bool, Optional[str]]:
        """Validira API key za datog provajdera.

        Args:
            provider: Ime provajdera (openai, claude, itd.)
            api_key: API ključ za validaciju

        Returns:
            (True, None) ako je validan
            (False, error_message) ako nije validan
        """
        if not api_key:
            if provider == "ollama":
                return True, None  # Ollama doesn't require key
            return False, "API ključ je prazan"

        if provider not in cls.PROVIDER_PATTERNS:
            return False, f"Nepoznat provajder: {provider}"

        pattern = cls.PROVIDER_PATTERNS[provider]

        if provider == "ollama":
            if api_key in ["", "localhost:11434"]:
                return True, None
            return False, "Ollama ne zahteva API ključ"

        if not re.match(pattern, api_key):
            return False, f"Neispravan format API ključa za {provider}"

        return True, None

    @classmethod
    def get_supported_providers(cls) -> List[str]:
        """Vraća listu podržanih provajdera.

        Returns:
            Lista imena provajdera
        """
        return list(cls.PROVIDER_PATTERNS.keys())

    @classmethod
    def get_provider_models(cls, provider: str) -> List[str]:
        """Vraća listu modela za provajdera.

        Args:
            provider: Ime provajdera

        Returns:
            Lista dostupnih modela
        """
        return cls.PROVIDER_SCOPES.get(provider, [])

    @classmethod
    def validate_model(cls, provider: str, model: str) -> Tuple[bool, Optional[str]]:
        """Validira da li je model podržan za provajdera.

        Args:
            provider: Ime provajdera
            model: Ime modela

        Returns:
            (True, None) ako je podržan
            (False, error_message) ako nije
        """
        supported = cls.get_provider_models(provider)

        if not supported:
            return False, f"Nepoznat provajder: {provider}"

        model_lower = model.lower()
        for sup in supported:
            if model_lower in sup.lower():
                return True, None

        return (
            False,
            f"Model '{model}' nije podržan za {provider}. Podržani: {', '.join(supported)}",
        )

    @classmethod
    def get_provider_info(cls, provider: str) -> Dict[str, any]:
        """Vraća informacije o provajderu.

        Args:
            provider: Ime provajdera

        Returns:
            Dict sa informacijama
        """
        return {
            "provider": provider,
            "models": cls.PROVIDER_SCOPES.get(provider, []),
            "key_pattern": cls.PROVIDER_PATTERNS.get(provider, ""),
            "requires_key": provider != "ollama",
        }


class CloudAPIValidator:
    """Validacija za cloud API provajdere prema official dokumentaciji.

    Koristi zvanične API endpointe za validaciju ključeva.
    """

    @staticmethod
    async def validate_openai(api_key: str) -> Tuple[bool, Optional[str]]:
        """Validira OpenAI API key.

        Koristi /v1/models endpoint za validaciju.
        """
        import httpx

        if not api_key.startswith("sk-"):
            return False, "OpenAI ključ mora početi sa 'sk-'"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                if response.status_code == 200:
                    return True, None
                elif response.status_code == 401:
                    return False, "Neispravan OpenAI API ključ"
                else:
                    return False, f"OpenAI greška: {response.status_code}"
        except Exception as e:
            return False, f"Validacija neuspešna: {e}"

    @staticmethod
    async def validate_anthropic(api_key: str) -> Tuple[bool, Optional[str]]:
        """Validira Anthropic (Claude) API key."""
        import httpx

        if not api_key.startswith("sk-ant-"):
            return False, "Claude ključ mora početi sa 'sk-ant-'"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.anthropic.com/v1/messages/models",
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                )
                if response.status_code == 200:
                    return True, None
                elif response.status_code == 401:
                    return False, "Neispravan Claude API ključ"
                else:
                    return False, f"Claude greška: {response.status_code}"
        except Exception as e:
            return False, f"Validacija neuspešna: {e}"

    @staticmethod
    async def validate_google(api_key: str) -> Tuple[bool, Optional[str]]:
        """Validira Google Gemini API key."""
        import httpx

        if len(api_key) < 30:
            return False, "Gemini ključ je prekratak"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
                )
                if response.status_code == 200:
                    return True, None
                elif response.status_code == 403:
                    return False, "Neispravan Gemini API ključ"
                else:
                    return False, f"Gemini greška: {response.status_code}"
        except Exception as e:
            return False, f"Validacija neuspešna: {e}"

    @classmethod
    async def validate_provider(
        cls, provider: str, api_key: str
    ) -> Tuple[bool, Optional[str]]:
        """Validira API key za provajdera koristeći cloud API.

        Args:
            provider: Ime provajdera
            api_key: API ključ

        Returns:
            (True, None) ako je validan
        """
        validators = {
            "openai": cls.validate_openai,
            "claude": cls.validate_anthropic,
            "gemini": cls.validate_google,
        }

        validator = validators.get(provider)
        if validator:
            return await validator(api_key)

        return True, None
