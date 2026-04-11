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
# noqa: F401 - intentionally re-exported for backwards compatibility
from app.services.quiz import (
    BaseQuizClient,  # noqa: F401
    ClaudeQuizClient,  # noqa: F401
    OllamaQuizClient,  # noqa: F401
    OpenAICompatQuizClient,  # noqa: F401
    OpenAIQuizClient,  # noqa: F401
    _fallback_questions,  # noqa: F401
    _parse_questions,  # noqa: F401
    _validate_questions,  # noqa: F401
    detect_subject_area,  # noqa: F401
    get_available_providers,  # noqa: F401
    get_clients,  # noqa: F401
    get_images_for_chunks,  # noqa: F401
    get_quiz_usage_stats,  # noqa: F401
    get_provider,  # noqa: F401
    get_specialized_prompt,  # noqa: F401
    is_chunk_quality,  # noqa: F401
    mark_chunks_as_used,  # noqa: F401
    QUIZ_PROMPT,  # noqa: F401
    QuizService,  # noqa: F401
    quiz_service,  # noqa: F401
    select_chunks_for_quiz,  # noqa: F401
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
