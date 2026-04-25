# -*- coding: utf-8 -*-
"""
================================================================================
CELERY APPLICATION
================================================================================
Konfiguracija Celery task queue sistema.

Verzija: 1.1.0
================================================================================
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Kreiranje Celery aplikacije
_config = settings.CELERY_CONFIG
celery_app = Celery(
    "ai_learning_system",
    broker=_config.pop("broker_url"),
    backend=_config.pop("result_backend"),
)
celery_app.conf.update(_config)

# Autodiscover task-ova
celery_app.autodiscover_tasks(["app.workers.tasks"])

# Celery Beat schedule (periodični task-ovi)
celery_app.conf.beat_schedule = {
    # Čišćenje starih fajlova — jednom dnevno
    "cleanup-old-files": {
        "task": "app.workers.tasks.cleanup_old_files",
        "schedule": 86400.0,
    },
    # Dnevni podsetnici — svakih sat (task interno filtrira po reminder_time)
    "send-study-reminders": {
        "task": "app.workers.tasks.send_study_reminders",
        "schedule": 3600.0,
    },
    # Nedeljni sažeci — svake nedelje u 10:00
    "send-weekly-summaries": {
        "task": "app.workers.tasks.send_weekly_summaries",
        "schedule": crontab(hour=10, minute=0, day_of_week=0),
    },
    # Indeksiranje MD dokumentacije — svaki dan u 02:00
    "crawl-project-docs-daily": {
        "task": "crawl_project_docs_task",
        "schedule": crontab(hour=2, minute=0),
    },
}
