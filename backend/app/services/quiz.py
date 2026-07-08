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
from app.services.quiz import (  # noqa: F401
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

