# -*- coding: utf-8 -*-
"""
================================================================================
CELERY APPLICATION
================================================================================
Konfiguracija Celery task queue sistema.

Verzija: 1.0.0
================================================================================
"""

from celery import Celery
from app.core.config import settings

# Kreiranje Celery aplikacije
celery_app = Celery(
    "ai_learning_system",
    **settings.CELERY_CONFIG
)

# Autodiscover task-ova
celery_app.autodiscover_tasks(["app.workers.tasks"])

# Celery Beat schedule (periodični task-ovi)
celery_app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "app.workers.tasks.cleanup_old_files",
        "schedule": 86400.0,  # Jednom dnevno
    },
    "send-study-reminders": {
        "task": "app.workers.tasks.send_study_reminders",
        "schedule": 3600.0,  # Svaki sat
    },
}
