# -*- coding: utf-8 -*-
"""
================================================================================
TASKS - MAIN MODULE
================================================================================
Modularizovana verzija Celery task-ova.

Svi taskovi se re-exportuju za backward compatibility.
Originalni tasks.py je i dalje dostupan.

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

# PDF Processing tasks
from app.workers.tasks.pdf_processing import (  # noqa: F401
    process_pdf_task,
    get_db_session as _pdf_get_db_session,
)

# PDF Export tasks
from app.workers.tasks.pdf_export import (  # noqa: F401
    export_pdf_task,
    get_db_session as _pdf_export_get_db_session,
)

# DOCX Export tasks (optional - requires python-docx)
try:
    from app.workers.tasks.docx_export import (  # noqa: F401
        export_docx_task,
        get_db_session as _docx_export_get_db_session,
    )
except ImportError:
    import logging as _logging

    _logging.getLogger(__name__).warning(
        "DOCX export tasks unavailable (python-docx not installed)"
    )
    export_docx_task = None
    _docx_export_get_db_session = None

# Translation tasks
from app.workers.tasks.translation import (  # noqa: F401
    translate_document_task,
    translate_with_fallback,
    get_db_session as _trans_get_db_session,
)

# Quiz tasks
from app.workers.tasks.quiz import (  # noqa: F401
    generate_quiz_task,
    auto_pipeline_task,
    get_db_session as _quiz_get_db_session,
)

# Maintenance tasks
from app.workers.tasks.maintenance import (
    cleanup_old_files,
    cleanup_old_sessions_task,
    cache_warming_task,
    send_study_reminders,
    send_weekly_summaries,
)

# Knowledge tasks
from app.workers.tasks.knowledge import (
    index_document_task,
    crawl_project_docs_task,
    crawl_url_task,
    crawl_site_task,
)


def get_db_session():
    """
    Kreira SQLAlchemy session za task.
    Wrapper funkcija za backward compatibility.
    """
    from sqlalchemy.orm import sessionmaker
    from app.db.session import engine

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


__all__ = [
    # PDF Processing
    "process_pdf_task",
    # PDF Export
    "export_pdf_task",
    # DOCX Export
    "export_docx_task",
    # Translation
    "translate_document_task",
    "translate_with_fallback",
    # Quiz
    "generate_quiz_task",
    "auto_pipeline_task",
    # Maintenance
    "cleanup_old_files",
    "cleanup_old_sessions_task",
    "cache_warming_task",
    "send_study_reminders",
    "send_weekly_summaries",
    # Knowledge
    "index_document_task",
    "crawl_project_docs_task",
    "crawl_url_task",
    "crawl_site_task",
    # Helpers
    "get_db_session",
]
