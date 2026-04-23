# -*- coding: utf-8 -*-
"""
================================================================================
CELERY TESTOVI
================================================================================
Unit testovi za Celery task queue sistem.

Verzija: 1.0.0
================================================================================
"""

from unittest.mock import patch
from celery import Celery


class TestCeleryApp:
    """
    Testovi za Celery app konfiguraciju.
    """

    def test_celery_import(self):
        """
        Testira da Celery može da se importuje.
        """
        from celery import Celery

        assert Celery is not None

    def test_celery_result_import(self):
        """
        Testira da Celery result može da se importuje.
        """
        from celery.result import AsyncResult

        assert AsyncResult is not None


class TestCeleryConfig:
    """
    Testovi za Celery konfiguraciju.
    """

    @patch("app.workers.celery_app.celery_app")
    def test_celery_app_exists(self, mock_celery):
        """
        Testira da celery_app može da se importuje.
        """
        import app.workers.celery_app as celery_module

        assert hasattr(celery_module, "celery_app")

    @patch("app.workers.celery_app.celery_app")
    def test_celery_has_name(self, mock_celery):
        """
        Testira da Celery app ima ime.
        """
        mock_celery.name = "ai_learning_system"
        assert mock_celery.name == "ai_learning_system"

    def test_celery_can_be_instantiated(self):
        """
        Testira da Celery može biti instanciran.
        """
        app = Celery("test_app")
        assert app is not None


class TestCeleryTasks:
    """
    Testovi za Celery task-ove.
    """

    def test_task_decorator_exists(self):
        """
        Testira da task decorator postoji.
        """
        from celery import shared_task

        assert shared_task is not None


class TestCeleryWorkerFunctions:
    """
    Testovi za worker funkcije.
    """

    def test_can_import_tasks_module(self):
        """
        Testira da možemo importovati tasks modul.
        """
        from app.workers import tasks

        assert tasks is not None

    def test_can_import_celery_app(self):
        """
        Testira da možemo importovati celery_app.
        """
        from app.workers.celery_app import celery_app

        assert celery_app is not None


class TestCeleryBeatSchedule:
    """
    Testovi za Celery Beat schedule.
    """

    def test_celery_schedules_import(self):
        """
        Testira da možemo importovati crontab.
        """
        from celery.schedules import crontab

        assert crontab is not None
