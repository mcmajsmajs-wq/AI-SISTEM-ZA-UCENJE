from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
import httpx
import logging

from app.core.config import settings
from app.db.models.user import User
from app.services.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

PROVIDERS = [
    {"id": "openai", "name": "OpenAI", "base_url": "https://api.openai.com/v1/models", "model": None, "key_attr": "OPENAI_API_KEY"},
    {"id": "groq", "name": "Groq", "base_url": "https://api.groq.com/openai/v1/chat/completions", "model": "llama-3.1-8b-instant", "key_attr": "GROQ_API_KEY"},
    {"id": "mistral", "name": "Mistral", "base_url": "https://api.mistral.ai/v1/chat/completions", "model": "mistral-small-latest", "key_attr": "MISTRAL_API_KEY"},
    {"id": "claude", "name": "Claude", "base_url": "https://api.anthropic.com/v1/messages", "model": "claude-3-haiku-20240307", "key_attr": "ANTHROPIC_API_KEY"},
    {"id": "deepseek", "name": "DeepSeek", "base_url": "https://api.deepseek.com/v1/chat/completions", "model": "deepseek-chat", "key_attr": "DEEPSEEK_API_KEY"},
    {"id": "gemini", "name": "Gemini", "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "model": "gemini-2.0-flash", "key_attr": "GEMINI_API_KEY"},
    {"id": "ollama", "name": "Ollama (lokalni)", "base_url": None, "model": None, "key_attr": None},
]

USER_KEY_MAP = {
    "openai": "ai_api_key_openai",
    "groq": "ai_api_key_groq",
    "mistral": "ai_api_key_mistral",
    "claude": "ai_api_key_claude",
    "deepseek": "ai_api_key_deepseek",
    "gemini": "ai_api_key_gemini",
}

class ProviderStatus(BaseModel):
    id: str
    name: str
    status: str
    available: bool
    system_key_set: bool
    user_key_set: bool
    message: str

class ProvidersHealthResponse(BaseModel):
    providers: list[ProviderStatus]
    summary: str


@router.get("/health", response_model=ProvidersHealthResponse)
async def providers_health(current_user: Optional[User] = Depends(get_current_user)):
    results = []
    for prov in PROVIDERS:
        pid = prov["id"]

        user_key = None
        user_key_set = False
        if current_user and pid in USER_KEY_MAP:
            user_key = getattr(current_user, USER_KEY_MAP[pid], None)
            user_key_set = bool(user_key)

        system_key = None
        system_key_set = False
        if prov["key_attr"]:
            system_key = getattr(settings, prov["key_attr"], None)
            system_key_set = bool(system_key)

        api_key = user_key or system_key

        if pid == "ollama":
            status, msg = await _check_ollama()
        elif api_key:
            status, msg = await _check_provider_api(pid, api_key, prov)
        else:
            status, msg = "missing_key", "API ključ nije podešen"

        results.append(ProviderStatus(
            id=pid,
            name=prov["name"],
            status=status,
            available=status == "ok",
            system_key_set=system_key_set,
            user_key_set=user_key_set,
            message=msg,
        ))

    available = sum(1 for r in results if r.available)
    total = len(results)
    summary = f"{available}/{total} provajdera dostupno"

    return ProvidersHealthResponse(providers=results, summary=summary)


async def _check_ollama():
    try:
        host = getattr(settings, "OLLAMA_HOST", "http://ollama:11434")
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{host}/api/tags")
            if resp.status_code == 200:
                return "ok", "Ollama servis radi"
            return "error", f"Ollama odgovara sa {resp.status_code}"
    except httpx.ConnectError:
        return "unavailable", "Ollama nije pokrenut"
    except Exception as e:
        return "error", f"Greška: {e}"


async def _check_provider_api(pid, api_key, prov):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if pid == "openai":
                resp = await client.get(
                    prov["base_url"],
                    headers={"Authorization": f"Bearer {api_key}"},
                )
            elif pid == "claude":
                resp = await client.post(
                    prov["base_url"],
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": prov["model"],
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                )
            else:
                resp = await client.post(
                    prov["base_url"],
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": prov["model"],
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1,
                    },
                )

            if resp.status_code == 200:
                return "ok", f"{prov['name']}: API ključ validan"
            elif resp.status_code == 401:
                return "invalid_key", f"{prov['name']}: API ključ nije validan ili je istekao"
            elif resp.status_code == 402:
                return "insufficient_balance", f"{prov['name']}: Nema dovoljno kredita"
            elif resp.status_code == 403:
                return "forbidden", f"{prov['name']}: Pristup odbijen"
            elif resp.status_code == 429:
                return "rate_limited", f"{prov['name']}: Prekoračen limit zahteva"
            else:
                return "error", f"{prov['name']}: {resp.status_code} - {resp.text[:100]}"

    except httpx.TimeoutException:
        return "timeout", f"{prov['name']}: Server ne odgovara (timeout)"
    except httpx.ConnectError:
        return "unavailable", f"{prov['name']}: Nepristupačan server"
    except Exception as e:
        logger.warning(f"Health check error for {pid}: {e}")
        return "error", f"{prov['name']}: Greška pri proveri"
