# -*- coding: utf-8 -*-
"""
===============================================================================
QUIZ CLIENTS - FACTORY AND EXPORTS
===============================================================================
Factory funkcije za kreiranje AI klijenata za quiz generaciju.

Verzija: 1.0.0
===============================================================================
"""

from typing import Dict, Optional, List

from app.services.quiz.clients.base import BaseQuizClient
from app.services.quiz.clients.ollama import OllamaQuizClient
from app.services.quiz.clients.openai import OpenAIQuizClient
from app.services.quiz.clients.claude import ClaudeQuizClient
from app.services.quiz.clients.openai_compat import OpenAICompatQuizClient
from app.core.config import settings


# Redosled pokušaja: prvi dostupan pobedi
_PROVIDER_ORDER = [
    "groq",
    "openai",
    "claude",
    "gemini",
    "mistral",
    "deepseek",
    "ollama",
]


def _build_clients(
    user_openai_key: str = None,
    user_claude_key: str = None,
    user_gemini_key: str = None,
    user_groq_key: str = None,
    user_mistral_key: str = None,
    user_deepseek_key: str = None,
) -> Dict[str, BaseQuizClient]:
    """
    Kreira dictionary svih AI klijenata sa opcionalnim override-om korisničkih ključeva.

    Priority:
    1. User's own API key (from user settings)
    2. System API key from settings (SYSTEM_GROQ_API_KEY, etc.)
    3. Default API key from settings (GROQ_API_KEY, etc.)

    Args:
        user_openai_key: Korisnikov OpenAI API ključ
        user_claude_key: Korisnikov Claude API ključ
        user_gemini_key: Korisnikov Gemini API ključ
        user_groq_key: Korisnikov Groq API ključ
        user_mistral_key: Korisnikov Mistral API ključ
        user_deepseek_key: Korisnikov DeepSeek API ključ

    Returns:
        Dict[str, BaseQuizClient]: Dictionary svih klijenata
    """
    # Prioritet: 1. Korisnikov ključ, 2. Default ključ iz .env
    gemini_key = user_gemini_key or getattr(settings, "GEMINI_API_KEY", "") or ""
    groq_key = user_groq_key or getattr(settings, "GROQ_API_KEY", "") or ""
    mistral_key = user_mistral_key or getattr(settings, "MISTRAL_API_KEY", "") or ""
    openai_key = user_openai_key or getattr(settings, "OPENAI_API_KEY", "") or ""
    claude_key = user_claude_key or getattr(settings, "ANTHROPIC_API_KEY", "") or ""
    deepseek_key = user_deepseek_key or getattr(settings, "DEEPSEEK_API_KEY", "") or ""

    ollama = OllamaQuizClient()
    openai = OpenAIQuizClient()
    if user_openai_key:
        openai.api_key = user_openai_key
    claude = ClaudeQuizClient()
    if user_claude_key:
        claude.api_key = user_claude_key

    return {
        "ollama": ollama,
        "openai": openai,
        "claude": claude,
        "gemini": OpenAICompatQuizClient(
            "gemini",
            "https://generativelanguage.googleapis.com/v1beta/openai",
            "gemini-2.0-flash",
            gemini_key,
        ),
        "groq": OpenAICompatQuizClient(
            "groq",
            "https://api.groq.com/openai/v1",
            "llama-3.3-70b-versatile",
            groq_key,
        ),
        "mistral": OpenAICompatQuizClient(
            "mistral", "https://api.mistral.ai/v1", "mistral-small-latest", mistral_key
        ),
        "deepseek": OpenAICompatQuizClient(
            "deepseek", "https://api.deepseek.com/v1", "deepseek-chat", deepseek_key
        ),
    }


def get_provider(name: str, **kwargs) -> Optional[BaseQuizClient]:
    """
    Vraća specifičnog provider klijenta.

    Args:
        name: Naziv providera (ollama, openai, claude, gemini, groq, mistral, deepseek)
        **kwargs: Opcioni korisnički API ključevi

    Returns:
        Optional[BaseQuizClient]: Provider klijent ili None
    """
    clients = _build_clients(**kwargs)
    return clients.get(name)


def get_available_providers() -> List[dict]:
    """
    Vraća listu svih provajdera i njihove dostupnosti.

    Returns:
        List[dict]: Lista sa informacijama o svakom provideru
    """
    clients = _build_clients()
    return [
        {
            "id": k,
            "available": v.is_available(),
            "type": "local" if k == "ollama" else "online",
        }
        for k, v in clients.items()
    ]


# Global cached clients - koristi se kao default
_CLIENTS: Dict[str, BaseQuizClient] = _build_clients()


def get_clients() -> Dict[str, BaseQuizClient]:
    """
    Vraća keširane klijente (singleton).

    Returns:
        Dict[str, BaseQuizClient]: Dictionary svih klijenata
    """
    return _CLIENTS