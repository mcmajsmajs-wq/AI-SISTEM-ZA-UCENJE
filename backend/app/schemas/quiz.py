# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - QUIZ SISTEM
================================================================================
Verzija: 1.0.0
================================================================================
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any


# ============================================================
# QUESTION SCHEMAS
# ============================================================


class QuestionCreate(BaseModel):
    """Kreiranje pitanja."""

    question_text: str = Field(..., min_length=5)
    question_type: str = Field(
        "multiple_choice",
        pattern="^(multiple_choice|checkbox|true_false|fill_blank|calculation|step_by_step|text_input|sequencing|categorization|matching|odd_one_out)$",  # noqa: E501
    )
    options: List[str] = Field(..., min_length=2)
    correct_answer: str
    explanation: Optional[str] = None
    points: int = Field(1, ge=1)
    order_index: int = 0
    # Dodatna polja za fill_blank tip
    exact_word: Optional[str] = None
    alternative_words: Optional[List[str]] = None
    case_insensitive: bool = True
    # Polja za calculation i step_by_step
    formula: Optional[str] = None
    steps: Optional[List[str]] = None


class QuestionResponse(BaseModel):
    """Pitanje za prikaz sa tačnim odgovorom i objašnjenjem."""

    id: str
    quiz_id: str
    question_text: str
    question_type: str
    options: List[str]
    points: int
    order_index: int
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    # Dodatna polja za fill_blank tip
    exact_word: Optional[str] = None
    alternative_words: Optional[List[str]] = None
    case_insensitive: bool = True
    # Polja za calculation i step_by_step
    formula: Optional[str] = None
    steps: Optional[List[str]] = None

    class Config:
        from_attributes = True


class QuestionWithAnswer(QuestionResponse):
    """Pitanje sa tačnim odgovorom (za prikaz rezultata)."""

    correct_answer: str
    explanation: Optional[str] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None


# ============================================================
# QUIZ SCHEMAS
# ============================================================


class QuizCreate(BaseModel):
    """Pokretanje generisanja kviza."""

    document_id: str
    num_questions: int = Field(
        0,
        ge=0,
        le=30,
        description="Broj pitanja (0 = automatski na osnovu veličine dokumenta)",
    )
    time_limit: Optional[int] = Field(None, ge=60, description="Vreme u sekundama")
    passing_score: int = Field(60, ge=1, le=100)
    shuffle_questions: bool = Field(False, description="Mešanje redosleda pitanja")
    provider: Optional[str] = Field(
        None, description="AI provajder: ollama|openai|claude (None=auto)"
    )
    source_content: Optional[str] = Field(
        None,
        description=(
            "Izvor teksta za kviz: 'translated' (srpski) ili 'original' "
            "(engleski). None = auto (koristi prevedeno ako postoji)"
        ),
    )


class QuizResponse(BaseModel):
    """Kviz za prikaz."""

    id: str
    document_id: str
    user_id: str
    title: str
    description: Optional[str] = None
    subject_area: Optional[str] = None  # Oblast dokumenta
    total_questions: int
    target_questions: Optional[int] = 0
    time_limit: Optional[int] = None
    passing_score: Optional[int] = 60  # Default to 60%
    shuffle_questions: bool = False
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuizWithQuestions(QuizResponse):
    """Kviz sa listom pitanja (bez odgovora)."""

    questions: List[QuestionResponse] = []


class QuizListResponse(BaseModel):
    """Paginisana lista kvizova."""

    items: List[QuizResponse]
    total: int
    skip: int
    limit: int


# ============================================================
# ATTEMPT SCHEMAS
# ============================================================


class AnswerSubmit(BaseModel):
    """Jedan odgovor u submitu."""

    question_id: str
    user_answer: str  # za checkbox — comma-separated vrednosti


class AttemptSubmit(BaseModel):
    """Submitovanje celog kviza."""

    answers: List[AnswerSubmit]


class AnswerResult(BaseModel):
    """Rezultat jednog odgovora."""

    question_id: str
    user_answer: str
    correct_answer: str
    is_correct: bool
    points_earned: int
    explanation: Optional[str] = None


class AttemptResponse(BaseModel):
    """Rezultat pokušaja."""

    id: str
    quiz_id: str
    user_id: str
    score: int
    total_points: int
    percentage: float
    passed: bool
    started_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttemptResult(AttemptResponse):
    """Detaljan rezultat sa odgovorima."""

    answers: List[AnswerResult] = []
    xp_awarded: Optional[int] = None
    leveled_up: Optional[bool] = None
    new_level: Optional[int] = None
    new_badges: Optional[List[dict]] = None


class AttemptListResponse(BaseModel):
    """Lista pokušaja."""

    items: List[AttemptResponse]
    total: int


# ============================================================
# PIPELINE SCHEMAS
# ============================================================


class PipelineRequest(BaseModel):
    """Pokretanje automatskog pipeline-a: PDF → prevod → kviz."""

    file_id: Optional[str] = None  # ako fajl već postoji
    document_id: Optional[str] = None  # ako dokument već postoji
    source_language: str = "en"
    target_language: str = "sr"
    translation_provider: Optional[str] = Field(
        None, description="ollama|deepl|openai|google|claude"
    )
    quiz_provider: Optional[str] = Field(None, description="ollama|openai|claude")
    num_questions: int = Field(
        0, ge=0, le=30, description="Broj pitanja (0 = automatski)"
    )
    skip_translation: bool = False
    passing_score: int = Field(60, ge=1, le=100)


class PipelineStatus(BaseModel):
    """Status automatskog pipeline-a."""

    pipeline_id: str
    document_id: Optional[str] = None
    quiz_id: Optional[str] = None
    stage: (
        str  # pending | processing_pdf | translating | generating_quiz | done | error
    )
    progress: int = 0  # 0-100
    message: str = ""
    error: Optional[str] = None
    providers_used: Optional[Any] = None
