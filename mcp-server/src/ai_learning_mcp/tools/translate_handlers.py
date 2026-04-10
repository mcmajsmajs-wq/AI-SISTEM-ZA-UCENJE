# -*- coding: utf-8 -*-
"""
Translation Tool Handlers - FAZA 7
Handlers za Translation MCP alate.
"""

import os
from typing import Any, Dict, Optional
import httpx


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English"},
    {"code": "sr", "name": "Serbian"},
    {"code": "de", "name": "German"},
    {"code": "fr", "name": "French"},
    {"code": "es", "name": "Spanish"},
    {"code": "it", "name": "Italian"},
    {"code": "ru", "name": "Russian"},
    {"code": "zh", "name": "Chinese"},
    {"code": "ja", "name": "Japanese"},
    {"code": "ko", "name": "Korean"},
    {"code": "ar", "name": "Arabic"},
    {"code": "pt", "name": "Portuguese"},
    {"code": "nl", "name": "Dutch"},
    {"code": "pl", "name": "Polish"},
    {"code": "hu", "name": "Hungarian"},
]


async def handle_translate_text(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za translate_text tool."""
    text = params["text"]
    source_language = params["source_language"]
    target_language = params["target_language"]
    provider = params.get("provider", "openai")
    user_api_key = params.get("user_api_key")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/translate/",
                headers=headers,
                json={
                    "text": text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "provider": provider,
                    "user_api_key": user_api_key,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "translated_text": data.get("translated_text"),
                    "source_language": source_language,
                    "target_language": target_language,
                }
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_translate_batch(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za translate_batch tool."""
    texts = params["texts"]
    source_language = params["source_language"]
    target_language = params["target_language"]
    provider = params.get("provider", "openai")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/translate/batch",
                headers=headers,
                json={
                    "texts": texts,
                    "source_language": source_language,
                    "target_language": target_language,
                    "provider": provider,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "translations": data.get("translations", []),
                    "count": len(texts),
                }
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_translate_supported_languages() -> Dict[str, Any]:
    """Handler za translate_supported_languages tool."""
    return {
        "status": "ok",
        "languages": SUPPORTED_LANGUAGES,
        "count": len(SUPPORTED_LANGUAGES),
    }
