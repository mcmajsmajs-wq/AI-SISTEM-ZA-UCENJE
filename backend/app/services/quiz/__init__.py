# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ MODULE - EXPORTS
================================================================================

Verzija: 1.0.0
================================================================================
"""

# Prompts
from app.services.quiz.prompts.quiz_prompt import QUIZ_PROMPT
from app.services.quiz.prompts.subjects import (
    get_specialized_prompt,
    get_subject_instruction,
    get_all_subjects as prompts_get_all_subjects,
)

# Helpers - parsing & validation
from app.services.quiz.helpers import (
    _parse_questions,
    _validate_questions,
    _fallback_questions,
    is_chunk_quality,
    select_chunks_for_quiz,
    get_images_for_chunks,
    get_quiz_usage_stats,
    mark_chunks_as_used,
)

# Helpers - subject detection
from app.services.quiz.helpers.subject_detection import (
    detect_subject_area,
    get_subject_keywords,
    get_all_subjects as subject_detection_get_all_subjects,
    SUBJECT_KEYWORDS,
)

# Helpers - document structure
from app.services.quiz.helpers.document_structure import (
    detect_document_structure,
    get_structure_based_prompt,
    get_structure_keywords,
    get_all_structures,
    STRUCTURE_PATTERNS,
)

# Helpers - progress tracking
from app.services.quiz.helpers.progress import (
    update_quiz_progress,
    get_quiz_progress,
    delete_quiz_progress,
    set_quiz_cache,
    get_quiz_cache,
    clear_quiz_cache,
)

# Clients
from app.services.quiz.clients import (
    BaseQuizClient,
    OllamaQuizClient,
    OpenAIQuizClient,
    ClaudeQuizClient,
    OpenAICompatQuizClient,
    get_provider,
    get_available_providers,
    get_clients,
)

# Service - import directly to avoid lazy loading issues
from app.services.quiz.service import (
    QuizService,
    quiz_service,
    _check_answer_static,
)

# Tasks - backward compatibility
from app.workers.tasks import (
    generate_quiz_task,
    auto_pipeline_task,
)

__all__ = [
    # Prompts
    "QUIZ_PROMPT",
    "get_specialized_prompt",
    "get_subject_instruction",
    # Helpers - parsing
    "_parse_questions",
    "_validate_questions",
    "_fallback_questions",
    "is_chunk_quality",
    "select_chunks_for_quiz",
    "get_images_for_chunks",
    "get_quiz_usage_stats",
    "mark_chunks_as_used",
    # Helpers - subject detection
    "detect_subject_area",
    "get_subject_keywords",
    "SUBJECT_KEYWORDS",
    # Helpers - document structure
    "detect_document_structure",
    "get_structure_based_prompt",
    "get_structure_keywords",
    "STRUCTURE_PATTERNS",
    # Helpers - progress
    "update_quiz_progress",
    "get_quiz_progress",
    "delete_quiz_progress",
    "set_quiz_cache",
    "get_quiz_cache",
    "clear_quiz_cache",
    # Clients
    "BaseQuizClient",
    "OllamaQuizClient",
    "OpenAIQuizClient",
    "ClaudeQuizClient",
    "OpenAICompatQuizClient",
    "get_provider",
    "get_available_providers",
    "get_clients",
    # Service
    "QuizService",
    "quiz_service",
    "_check_answer_static",
    # Tasks - backward compatibility
    "generate_quiz_task",
    "auto_pipeline_task",
]
