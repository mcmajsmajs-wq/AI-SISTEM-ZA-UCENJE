# -*- coding: utf-8 -*-
"""
Quiz helpers — re-exports from sub-modules.
"""

from app.services.quiz.helpers.parsing import (
    _get_attr,
    _get_chunk_id,
    _get_content,
    _is_used_for_quiz,
    _parse_questions,
    _validate_questions,
    _fallback_questions,
)

from app.services.quiz.helpers.selection import (
    LOW_QUALITY_PATTERNS,
    is_chunk_quality,
    chunk_quality_score,
    select_chunks_for_quiz,
    get_images_for_chunks,
    get_quiz_usage_stats,
    mark_chunks_as_used,
)

from app.services.quiz.helpers.subject_detection import (
    detect_subject_area,
    get_subject_keywords,
    SUBJECT_KEYWORDS,
    get_all_subjects as subject_detection_get_all_subjects,
)

from app.services.quiz.helpers.document_structure import (
    detect_document_structure,
    get_structure_based_prompt,
    get_structure_keywords,
    STRUCTURE_PATTERNS,
    get_all_structures as document_structure_get_all_structures,
)

from app.services.quiz.helpers.progress import (
    update_quiz_progress,
    get_quiz_progress,
    delete_quiz_progress,
    set_quiz_cache,
    get_quiz_cache,
    clear_quiz_cache,
)

parse_quiz_response = _parse_questions

__all__ = [
    "_parse_questions",
    "_validate_questions",
    "_fallback_questions",
    "_get_attr",
    "_get_chunk_id",
    "_get_content",
    "_is_used_for_quiz",
    "is_chunk_quality",
    "chunk_quality_score",
    "select_chunks_for_quiz",
    "get_images_for_chunks",
    "get_quiz_usage_stats",
    "mark_chunks_as_used",
    "LOW_QUALITY_PATTERNS",
    "parse_quiz_response",
    "detect_subject_area",
    "get_subject_keywords",
    "SUBJECT_KEYWORDS",
    "detect_document_structure",
    "get_structure_based_prompt",
    "get_structure_keywords",
    "STRUCTURE_PATTERNS",
    "update_quiz_progress",
    "get_quiz_progress",
    "delete_quiz_progress",
    "set_quiz_cache",
    "get_quiz_cache",
    "clear_quiz_cache",
]
