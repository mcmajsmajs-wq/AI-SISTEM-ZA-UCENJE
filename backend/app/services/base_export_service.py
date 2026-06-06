from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
import logging

logger = logging.getLogger(__name__)


class BaseExportService(ABC):
    """Apstraktna bazna klasa za sve export servise.

    Shared funkcionalnost:
      - progress_callback i _report_progress
      - _get_content(chunk) — unified content extraction
      - _load_skill(category) — shared skill loading
      - generate() — @abstractmethod; svaki format implementira svoj
    """

    def __init__(self, progress_callback: Optional[Callable] = None):
        self._progress_callback = progress_callback

    def _report_progress(self, current: int, total: int, message: str):
        if self._progress_callback:
            try:
                self._progress_callback(current, total, message)
            except Exception:
                pass

    def _get_content(self, chunk: Dict[str, Any]) -> str:
        """Unified content extraction: translated > original > empty."""
        return (
            chunk.get("translated_content")
            or chunk.get("translated_text")
            or chunk.get("translated", "")
            or chunk.get("content")
            or chunk.get("original", "")
            or ""
        )

    def _load_skill(self, category: str) -> str:
        """Load skill prompt for the given category (pdf, docx, etc.)."""
        try:
            from app.services.skills.file_skills import get_file_skill

            skill = get_file_skill()
            if category == "pdf":
                return skill.get_pdf_prompt()
            elif category == "docx":
                return skill.get_docx_prompt()
            return ""
        except Exception as e:
            logger.warning(f"Could not load {category} skill: {e}")
            return ""

    @abstractmethod
    def generate(self, title: str, chunks: List[Dict[str, Any]], **kwargs) -> bytes:
        pass


class ExportServiceError(Exception):
    """Base exception for export service errors."""

    pass
