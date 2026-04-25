# -*- coding: utf-8 -*-
"""
================================================================================
QUIZ SERVICE
================================================================================
Servis za upravljanje kvizovima, pitanjima i pokušajima.

Verzija: 1.0.0
================================================================================
"""

import logging
import random
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models.quiz import Quiz, Question, QuizAttempt, Answer
from app.db.models.document import Document, Chunk
from app.schemas.quiz import (
    QuizCreate,
    QuizUpdate,
    QuestionCreate,
    QuestionUpdate,
    AnswerCreate,
    QuestionType,
    QuizDifficulty,
    QuizStatus,
    AttemptStatus,
)

logger = logging.getLogger(__name__)


class QuizService:
    """
    ================================================================================
    QUIZ SERVICE
    ================================================================================
    Servis za kreiranje, upravljanje i evaluaciju kvizova.
    ================================================================================
    """
    
    @staticmethod
    def create_quiz(db: Session, user_id: UUID, quiz_data: QuizCreate) -> Quiz:
        """
        Kreira novi kviz.
        
        Args:
            db: Database session
            user_id: ID korisnika
            quiz_data: Podaci za kreiranje kviza
            
        Returns:
            Kreirani Quiz objekat
        """
        quiz = Quiz(
            user_id=user_id,
            document_id=quiz_data.document_id,
            title=quiz_data.title,
            description=quiz_data.description,
            time_limit=quiz_data.time_limit,
            passing_score=quiz_data.passing_score,
            max_attempts=quiz_data.max_attempts,
            difficulty=quiz_data.difficulty.value,
            question_types=[qt.value for qt in quiz_data.question_types] if quiz_data.question_types else [],
            status=QuizStatus.DRAFT.value,
            total_questions=0,
        )
        
        db.add(quiz)
        db.commit()
        db.refresh(quiz)
        
        if quiz_data.questions:
            for i, question_data in enumerate(quiz_data.questions):
                question = Question(
                    quiz_id=quiz.id,
                    question_text=question_data.question_text,
                    question_type=question_data.question_type.value,
                    options=question_data.options,
                    correct_answer=question_data.correct_answer,
                    correct_answers=question_data.correct_answers,
                    explanation=question_data.explanation,
                    hint=question_data.hint,
                    points=question_data.points,
                    difficulty=question_data.difficulty.value,
                    order=i,
                )
                db.add(question)
            
            quiz.total_questions = len(quiz_data.questions)
            db.commit()
            db.refresh(quiz)
        
        logger.info(f"Created quiz {quiz.id} for user {user_id}")
        return quiz
    
    @staticmethod
    def get_quiz(db: Session, quiz_id: UUID, user_id: Optional[UUID] = None) -> Optional[Quiz]:
        """
        Dohvata kviz po ID-u.
        """
        query = db.query(Quiz).filter(Quiz.id == quiz_id)
        if user_id:
            query = query.filter(Quiz.user_id == user_id)
        return query.first()
    
    @staticmethod
    def list_quizzes(
        db: Session,
        user_id: UUID,
        page: int = 1,
        size: int = 20,
        status: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> tuple:
        """
        Lista kvizove sa paginacijom.
        
        Returns:
            Tuple (quizzes, total)
        """
        query = db.query(Quiz).filter(Quiz.user_id == user_id)
        
        if status:
            query = query.filter(Quiz.status == status)
        if difficulty:
            query = query.filter(Quiz.difficulty == difficulty)
        
        total = query.count()
        quizzes = query.order_by(Quiz.created_at.desc()).offset((page - 1) * size).limit(size).all()
        
        return quizzes, total
    
    @staticmethod
    def update_quiz(db: Session, quiz_id: UUID, quiz_data: QuizUpdate) -> Optional[Quiz]:
        """
        Ažurira kviz.
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return None
        
        update_data = quiz_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "status" and value:
                value = value.value
            if field == "difficulty" and value:
                value = value.value
            setattr(quiz, field, value)
        
        if quiz_data.status == QuizStatus.PUBLISHED and not quiz.published_at:
            quiz.published_at = datetime.utcnow()
        
        db.commit()
        db.refresh(quiz)
        
        logger.info(f"Updated quiz {quiz_id}")
        return quiz
    
    @staticmethod
    def delete_quiz(db: Session, quiz_id: UUID) -> bool:
        """
        Briše kviz.
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            return False
        
        db.delete(quiz)
        db.commit()
        
        logger.info(f"Deleted quiz {quiz_id}")
        return True
    
    @staticmethod
    def add_question(db: Session, quiz_id: UUID, question_data: QuestionCreate) -> Question:
        """
        Dodaje pitanje u kviz.
        """
        max_order = db.query(func.max(Question.order)).filter(Question.quiz_id == quiz_id).scalar() or -1
        
        question = Question(
            quiz_id=quiz_id,
            question_text=question_data.question_text,
            question_type=question_data.question_type.value,
            options=question_data.options,
            correct_answer=question_data.correct_answer,
            correct_answers=question_data.correct_answers,
            explanation=question_data.explanation,
            hint=question_data.hint,
            points=question_data.points,
            difficulty=question_data.difficulty.value,
            order=max_order + 1,
        )
        
        db.add(question)
        
        db.query(Quiz).filter(Quiz.id == quiz_id).update({
            Quiz.total_questions: Quiz.total_questions + 1
        })
        
        db.commit()
        db.refresh(question)
        
        return question
    
    @staticmethod
    def update_question(db: Session, question_id: UUID, question_data: QuestionUpdate) -> Optional[Question]:
        """
        Ažurira pitanje.
        """
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return None
        
        update_data = question_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "question_type" and value:
                value = value.value
            if field == "difficulty" and value:
                value = value.value
            setattr(question, field, value)
        
        db.commit()
        db.refresh(question)
        
        return question
    
    @staticmethod
    def delete_question(db: Session, question_id: UUID) -> bool:
        """
        Briše pitanje.
        """
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False
        
        quiz_id = question.quiz_id
        db.delete(question)
        
        db.query(Quiz).filter(Quiz.id == quiz_id).update({
            Quiz.total_questions: Quiz.total_questions - 1
        })
        
        db.commit()
        
        return True
    
    @staticmethod
    def get_questions_for_quiz(db: Session, quiz_id: UUID) -> List[Question]:
        """
        Dohvata sva pitanja za kviz.
        """
        return db.query(Question).filter(Question.quiz_id == quiz_id).order_by(Question.order).all()
    
    @staticmethod
    def start_attempt(db: Session, quiz_id: UUID, user_id: UUID) -> QuizAttempt:
        """
        Započinje novi pokušaj rešavanja kviza.
        """
        quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
        if not quiz:
            raise ValueError("Quiz not found")
        
        if quiz.status != QuizStatus.PUBLISHED.value:
            raise ValueError("Quiz is not published")
        
        attempts_count = db.query(QuizAttempt).filter(
            QuizAttempt.quiz_id == quiz_id,
            QuizAttempt.user_id == user_id
        ).count()
        
        if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
            raise ValueError("Maximum attempts reached")
        
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            user_id=user_id,
            status=AttemptStatus.IN_PROGRESS.value,
        )
        
        db.add(attempt)
        
        db.query(Quiz).filter(Quiz.id == quiz_id).update({
            Quiz.attempts_count: Quiz.attempts_count + 1
        })
        
        db.commit()
        db.refresh(attempt)
        
        logger.info(f"Started attempt {attempt.id} for quiz {quiz_id}")
        return attempt
    
    @staticmethod
    def submit_answer(
        db: Session,
        attempt_id: UUID,
        question_id: UUID,
        selected_answer: Optional[str] = None,
        selected_answers: Optional[List[str]] = None,
        text_answer: Optional[str] = None,
        time_spent: int = 0
    ) -> Answer:
        """
        Podnosi odgovor na pitanje.
        """
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt or attempt.status != AttemptStatus.IN_PROGRESS.value:
            raise ValueError("Invalid attempt")
        
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise ValueError("Question not found")
        
        existing = db.query(Answer).filter(
            Answer.attempt_id == attempt_id,
            Answer.question_id == question_id
        ).first()
        
        if existing:
            db.delete(existing)
            db.flush()
        
        is_correct = False
        points_earned = 0
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE.value:
            is_correct = selected_answer == question.correct_answer
        elif question.question_type == QuestionType.CHECKBOX.value:
            if selected_answers and question.correct_answers:
                is_correct = set(selected_answers) == set(question.correct_answers)
        elif question.question_type == QuestionType.TRUE_FALSE.value:
            is_correct = selected_answer == question.correct_answer
        elif question.question_type == QuestionType.SHORT_ANSWER.value:
            if text_answer and question.correct_answer:
                is_correct = text_answer.strip().lower() == question.correct_answer.strip().lower()
        
        if is_correct:
            points_earned = question.points
        
        answer = Answer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_answer=selected_answer,
            selected_answers=selected_answers,
            text_answer=text_answer,
            is_correct=is_correct,
            points_earned=points_earned,
            time_spent=time_spent,
        )
        
        db.add(answer)
        db.commit()
        db.refresh(answer)
        
        return answer
    
    @staticmethod
    def complete_attempt(db: Session, attempt_id: UUID) -> QuizAttempt:
        """
        Završava pokušaj i izračunava rezultat.
        """
        attempt = db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
        if not attempt or attempt.status != AttemptStatus.IN_PROGRESS.value:
            raise ValueError("Invalid attempt")
        
        answers = db.query(Answer).filter(Answer.attempt_id == attempt_id).all()
        
        total_points = 0
        earned_points = 0
        correct_count = 0
        wrong_count = 0
        total_time = 0
        
        questions = db.query(Question).filter(Question.quiz_id == attempt.quiz_id).all()
        total_points = sum(q.points for q in questions)
        
        for answer in answers:
            earned_points += answer.points_earned
            total_time += answer.time_spent
            if answer.is_correct:
                correct_count += 1
            else:
                wrong_count += 1
        
        skipped_count = len(questions) - len(answers)
        
        percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        passed = percentage >= attempt.quiz.passing_score
        
        attempt.score = earned_points
        attempt.total_points = total_points
        attempt.percentage = round(percentage, 2)
        attempt.passed = passed
        attempt.correct_answers = correct_count
        attempt.wrong_answers = wrong_count
        attempt.skipped_answers = skipped_count
        attempt.time_spent = total_time
        attempt.status = AttemptStatus.COMPLETED.value
        attempt.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(attempt)
        
        logger.info(f"Completed attempt {attempt_id}: score={earned_points}/{total_points}, passed={passed}")
        return attempt
    
    @staticmethod
    def get_attempt(db: Session, attempt_id: UUID) -> Optional[QuizAttempt]:
        """
        Dohvata pokušaj po ID-u.
        """
        return db.query(QuizAttempt).filter(QuizAttempt.id == attempt_id).first()
    
    @staticmethod
    def get_user_attempts(db: Session, user_id: UUID, quiz_id: Optional[UUID] = None) -> List[QuizAttempt]:
        """
        Dohvata sve pokušaje korisnika.
        """
        query = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)
        if quiz_id:
            query = query.filter(QuizAttempt.quiz_id == quiz_id)
        return query.order_by(QuizAttempt.started_at.desc()).all()
    
    @staticmethod
    def get_quiz_stats(db: Session, user_id: UUID) -> Dict[str, Any]:
        """
        Dohvata statistiku kvizova za korisnika.
        """
        total_quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).count()
        total_attempts = db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).count()
        
        completed_attempts = db.query(QuizAttempt).filter(
            QuizAttempt.user_id == user_id,
            QuizAttempt.status == AttemptStatus.COMPLETED.value
        ).all()
        
        avg_score = 0.0
        pass_rate = 0.0
        total_questions = 0
        
        if completed_attempts:
            avg_score = sum(a.percentage for a in completed_attempts) / len(completed_attempts)
            passed = sum(1 for a in completed_attempts if a.passed)
            pass_rate = (passed / len(completed_attempts)) * 100
            total_questions = sum(a.correct_answers + a.wrong_answers for a in completed_attempts)
        
        return {
            "total_quizzes": total_quizzes,
            "total_attempts": total_attempts,
            "average_score": round(avg_score, 2),
            "pass_rate": round(pass_rate, 2),
            "total_questions_answered": total_questions,
        }
    
    @staticmethod
    def generate_questions_from_chunks(
        db: Session,
        chunks: List[Chunk],
        num_questions: int = 10,
        question_types: Optional[List[QuestionType]] = None,
        difficulty: QuizDifficulty = QuizDifficulty.MEDIUM
    ) -> List[QuestionCreate]:
        """
        Generiše pitanja iz chunk-ova.
        Ovo je helper funkcija koja se koristi za AI generisanje.
        """
        questions = []
        
        if not question_types:
            question_types = [QuestionType.MULTIPLE_CHOICE]
        
        selected_chunks = random.sample(chunks, min(num_questions, len(chunks)))
        
        for i, chunk in enumerate(selected_chunks):
            q_type = random.choice(question_types)
            
            if q_type == QuestionType.MULTIPLE_CHOICE:
                question = QuestionCreate(
                    question_text=f"Based on the text: '{chunk.content[:200]}...', which statement is correct?",
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    options=["Option A", "Option B", "Option C", "Option D"],
                    correct_answer="Option A",
                    explanation="This is a generated question.",
                    points=1,
                    difficulty=difficulty,
                )
            elif q_type == QuestionType.TRUE_FALSE:
                question = QuestionCreate(
                    question_text=f"True or False: Based on the provided text...",
                    question_type=QuestionType.TRUE_FALSE,
                    options=["True", "False"],
                    correct_answer="True",
                    explanation="This is a generated question.",
                    points=1,
                    difficulty=difficulty,
                )
            else:
                question = QuestionCreate(
                    question_text="What is the main idea of this section?",
                    question_type=q_type,
                    correct_answer="Generated answer",
                    explanation="This is a generated question.",
                    points=2,
                    difficulty=difficulty,
                )
            
            questions.append(question)
        
        return questions


quiz_service = QuizService()
