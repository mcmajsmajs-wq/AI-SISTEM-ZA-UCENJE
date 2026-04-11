# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TASKS - BACKWARD COMPATIBILITY
================================================================================
Ova datoteka je zadržana za backwards compatibility.
Sva funkcionalnost je prebačena u modularni tasks/ direktorijum.

Novo: from app.workers.tasks import process_pdf_task
Staro: from app.workers.tasks import process_pdf_task (i dalje radi)

Verzija: 2.0.0 (FAZA 4 - Modularizacija)
================================================================================
"""

# Import flag_modified for backward compatibility test
# Koristi se u translation task za update JSON polja (document.file_metadata)
# noqa: F401 - intentionally imported for backward compatibility
from sqlalchemy.orm.attributes import flag_modified  # noqa: F401

# Re-export everything from the new modular structure for backwards compatibility
# noqa: F401 - intentionally re-exported for backward compatibility
from app.workers.tasks import (  # noqa: F401
    # PDF Processing
    process_pdf_task,
    # Translation
    translate_document_task,
    translate_with_fallback,
    # Quiz
    generate_quiz_task,
    auto_pipeline_task,
    # Maintenance
    cleanup_old_files,
    cleanup_old_sessions_task,
    cache_warming_task,
    send_study_reminders,
    send_weekly_summaries,
    # Knowledge
    index_document_task,
    crawl_project_docs_task,
    crawl_url_task,
    crawl_site_task,
    # Helpers
    get_db_session,
)
