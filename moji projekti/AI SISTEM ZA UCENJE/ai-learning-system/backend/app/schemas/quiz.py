# -*- coding: utf-8 -*-
"""
================================================================================
PYDANTIC SCHEMAS - QUIZ
================================================================================
Schema-e za kviz sistem.

Verzija: 1.0.0
================================================================================
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum


class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    CHECKBOX = "checkbox"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class QuizDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuizStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class AttemptStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class QuestionBase(BaseModel):
    question_text: str
    question_type: QuestionType = QuestionType.MULTIPLE_CHOICE
    options: Optional[List[str]] = None
    correct_answer: str
    correct_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    points: int = 1
    difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM


class QuestionCreate(QuestionBase):
    pass


class QuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    correct_answers: Optional[List[str]] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    points: Optional[int] = None
    difficulty: Optional[QuestionDifficulty] = None


class QuestionResponse(QuestionBase):
    id: UUID
    quiz_id: UUID
    order: int
    created_at: datetime
    
    model_config = {"from_attributes": True}


class QuestionForAttempt(BaseModel):
    id: UUID
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    points: int
    order: int
    
    model_config = {"from_attributes": True}


class AnswerBase(BaseModel):
    question_id: UUID
    selected_answer: Optional[str] = None
    selected_answers: Optional[List[str]] = None
    text_answer: Optional[str] = None


class AnswerCreate(AnswerBase):
    pass


class AnswerResponse(AnswerBase):
    id: UUID
    attempt_id: UUID
    is_correct: bool
    points_earned: int
    time_spent: int
    
    model_config = {"from_attributes": True}


class AnswerWithQuestion(AnswerResponse):
    question: QuestionResponse


class QuizBase(BaseModel):
    title: str
    description: Optional[str] = None
    time_limit: int = 0
    passing_score: int = 70
    max_attempts: int = 3
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM


class QuizCreate(QuizBase):
    document_id: Optional[UUID] = None
    question_types: Optional[List[QuestionType]] = None
    questions: Optional[List[QuestionCreate]] = None


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    time_limit: Optional[int] = None
    passing_score: Optional[int] = None
    max_attempts: Optional[int] = None
    difficulty: Optional[QuizDifficulty] = None
    status: Optional[QuizStatus] = None


class QuizResponse(QuizBase):
    id: UUID
    document_id: Optional[UUID] = None
    user_id: UUID
    total_questions: int
    question_types: List[str]
    status: QuizStatus
    attempts_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class QuizWithQuestions(QuizResponse):
    questions: List[QuestionResponse]


class QuizListResponse(BaseModel):
    quizzes: List[QuizResponse]
    total: int
    page: int
    size: int
    pages: int


class QuizAttemptBase(BaseModel):
    quiz_id: UUID


class QuizAttemptCreate(QuizAttemptBase):
    pass


class QuizAttemptResponse(BaseModel):
    id: UUID
    quiz_id: UUID
    user_id: UUID
    score: int
    total_points: int
    percentage: float
    passed: bool
    correct_answers: int
    wrong_answers: int
    skipped_answers: int
    time_spent: int
    status: AttemptStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class QuizAttemptWithAnswers(QuizAttemptResponse):
    answers: List[AnswerWithQuestion]


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_answer: Optional[str] = None
    selected_answers: Optional[List[str]] = None
    text_answer: Optional[str] = None
    time_spent: int = 0


class SubmitAnswerResponse(BaseModel):
    is_correct: bool
    points_earned: int
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


class CompleteAttemptResponse(BaseModel):
    attempt: QuizAttemptResponse
    correct_answers: int
    wrong_answers: int
    time_spent: int
    passed: bool


class QuizStats(BaseModel):
    total_quizzes: int
    total_attempts: int
    average_score: float
    pass_rate: float
    total_questions_answered: int


class QuizGenerateRequest(BaseModel):
    document_id: UUID
    title: Optional[str] = None
    num_questions: int = Field(default=10, ge=5, le=50)
    question_types: Optional[List[QuestionType]] = None
    difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    time_limit: int = Field(default=0, ge=0)
    passing_score: int = Field(default=70, ge=0, le=100)


class QuizGenerateResponse(BaseModel):
    quiz_id: UUID
    status: str
    message: str
