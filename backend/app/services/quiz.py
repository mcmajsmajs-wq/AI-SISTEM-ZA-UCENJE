# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE — BACKWARDS COMPATIBILITY
================================================================================

Ova datoteka je zadržana za backwards compatibility.
Sva funkcionalnost je prebačena u modularni quiz/ direktorijum.

Novo: from app.services.quiz import quiz_service, QuizService
Staro: from app.services.quiz import quiz_service (i dalje radi)

Verzija: 2.1.0
================================================================================
"""

# Re-export everything from the new modular structure for backwards compatibility
from app.services.quiz import (
    # Prompts
    QUIZ_PROMPT,
    # Helpers
    _parse_questions,
    _validate_questions,
    _fallback_questions,
    is_chunk_quality,
    select_chunks_for_quiz,
    get_images_for_chunks,
    get_quiz_usage_stats,
    mark_chunks_as_used,
    # Clients
    BaseQuizClient,
    OllamaQuizClient,
    OpenAIQuizClient,
    ClaudeQuizClient,
    OpenAICompatQuizClient,
    get_provider,
    get_available_providers,
    get_clients,
    # Service
    QuizService,
    quiz_service,
    detect_subject_area,
    get_specialized_prompt,
)


# Redis funkcije (nisu još prebačene u modul)
def _get_redis():
    """Get Redis connection for progress tracking."""
    import redis as redis_client
    from app.core.config import settings

    try:
        return redis_client.from_url(
            settings.REDIS_CONNECTION_URL, decode_responses=True
        )
    except Exception:
        return None


def update_quiz_progress(quiz_id: str, current: int, total: int):
    """Update quiz progress in Redis."""
    import redis as redis_lib
    from app.core.config import settings

    try:
        r = redis_lib.Redis.from_url(
            settings.REDIS_CONNECTION_URL, decode_responses=True
        )
        r.hset(
            f"quiz_progress:{quiz_id}",
            mapping={"current": str(current), "total": str(total)},
        )
        r.expire(f"quiz_progress:{quiz_id}", 3600)
        r.close()
    except Exception as e:
        import logging

        logging.getLogger(__name__).debug(f"Redis progress update failed: {e}")


def get_quiz_progress(quiz_id: str) -> tuple:
    """Get quiz progress from Redis. Returns (current, total)."""
    try:
        r = _get_redis()
        if r:
            data = r.hgetall(f"quiz_progress:{quiz_id}")
            if data:
                return int(data.get("current", 0)), int(data.get("total", 0))
    except Exception:
        pass
    return 0, 0
