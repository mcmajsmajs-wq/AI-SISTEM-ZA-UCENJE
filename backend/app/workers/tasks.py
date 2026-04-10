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
# flag_modified(document, "file_metadata") - koristi se u app.workers.tasks.translation
# flag_modified(document, "file_metadata") - koristi se u translation.py
# flag_modified(document, "file_metadata") - koristi se u translate_document_task

from sqlalchemy.orm.attributes import flag_modified

# Re-export everything from the new modular structure for backwards compatibility
from app.workers.tasks import (
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
