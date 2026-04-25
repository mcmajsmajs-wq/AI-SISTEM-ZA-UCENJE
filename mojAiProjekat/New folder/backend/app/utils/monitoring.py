# -*- coding: utf-8 -*-
"""
================================================================================
SYSTEM MONITOR - Praćenje akcija i grešaka
================================================================================
Alat za praćenje svih akcija i automatsko beleženje grešaka.
"""

import logging
import traceback
import functools
import time
from datetime import datetime
from typing import Callable, Any
import sys

logger = logging.getLogger(__name__)

class ActionLogger:
    """Logger za praćenje akcija u sistemu."""
    
    def __init__(self):
        self.actions = []
        self.errors = []
    
    def log_action(self, action_type: str, details: dict, status: str = "success"):
        """Beleži akciju."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "details": details,
            "status": status
        }
        self.actions.append(entry)
        
        if status == "error":
            self.errors.append(entry)
            logger.error(f"[{action_type}] GREŠKA: {details}")
        else:
            logger.info(f"[{action_type}] {status}: {details}")
    
    def log_error(self, action_type: str, error: Exception, context: dict = None):
        """Beleži grešku sa kompletnim traceback-om."""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": action_type,
            "error": str(error),
            "error_type": type(error).__name__,
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        self.errors.append(error_entry)
        
        logger.error(f"[{action_type}] GREŠKA: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return error_entry
    
    def get_actions(self, action_type: str = None, status: str = None):
        """Vraća filtrirane akcije."""
        result = self.actions
        if action_type:
            result = [a for a in result if a["type"] == action_type]
        if status:
            result = [a for a in result if a["status"] == status]
        return result
    
    def get_errors(self):
        """Vraća sve greške."""
        return self.errors
    
    def clear(self):
        """Čisti log."""
        self.actions.clear()
        self.errors.clear()

# Globalna instanca
action_logger = ActionLogger()


def log_action(action_type: str):
    """Dekorator za automatsko beleženje akcija."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            context = {
                "function": func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100]
            }
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                action_logger.log_action(
                    action_type=action_type,
                    details={
                        **context,
                        "duration_seconds": round(duration, 2),
                        "result": str(result)[:100] if result else None
                    },
                    status="success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                error_entry = action_logger.log_error(
                    action_type=action_type,
                    error=e,
                    context={
                        **context,
                        "duration_seconds": round(duration, 2)
                    }
                )
                
                # Baci dalje da se propagira
                raise
        
        return wrapper
    return decorator


def log_quiz_generation(provider: str, document_id: str, num_questions: int):
    """Beleži početak generisanja kviza."""
    action_logger.log_action(
        action_type="quiz_generation_start",
        details={
            "provider": provider,
            "document_id": document_id,
            "num_questions": num_questions
        },
        status="started"
    )


def log_quiz_progress(quiz_id: str, current: int, total: int, status: str = "in_progress"):
    """Beleži progres kviza."""
    action_logger.log_action(
        action_type="quiz_progress",
        details={
            "quiz_id": quiz_id,
            "current_question": current,
            "total_questions": total,
            "progress_percent": round(current/total*100, 1) if total > 0 else 0
        },
        status=status
    )


def log_quiz_complete(quiz_id: str, num_questions: int, provider: str, duration: float):
    """Beleži završetak kviza."""
    action_logger.log_action(
        action_type="quiz_generation_complete",
        details={
            "quiz_id": quiz_id,
            "num_questions": num_questions,
            "provider": provider,
            "duration_seconds": round(duration, 2)
        },
        status="completed"
    )


def log_pdf_processing(document_id: str, total_pages: int, status: str):
    """Beleži procesiranje PDF-a."""
    action_logger.log_action(
        action_type="pdf_processing",
        details={
            "document_id": document_id,
            "total_pages": total_pages
        },
        status=status
    )


def log_ocr_progress(document_id: str, current_page: int, total_pages: int, method: str):
    """Beleži progres OCR-a."""
    action_logger.log_action(
        action_type="ocr_progress",
        details={
            "document_id": document_id,
            "current_page": current_page,
            "total_pages": total_pages,
            "method": method,
            "progress_percent": round(current_page/total_pages*100, 1)
        },
        status="in_progress"
    )


def get_system_status():
    """Vraća trenutni status sistema."""
    return {
        "total_actions": len(action_logger.actions),
        "total_errors": len(action_logger.errors),
        "recent_actions": action_logger.actions[-10:],
        "recent_errors": action_logger.errors[-5:]
    }


if __name__ == "__main__":
    # Test
    action_logger.log_action("test", {"message": "Test poruka"}, "success")
    print(get_system_status())
