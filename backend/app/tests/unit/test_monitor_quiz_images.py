# -*- coding: utf-8 -*-
"""
================================================================================
MONITOR QUIZ IMAGES TESTS
================================================================================
Unit testovi za utils/monitor_quiz_images.py.

Pokretanje:
    pytest tests/unit/test_monitor_quiz_images.py -v
================================================================================
"""

import pytest


class TestCheckQuizImages:
    """Testovi za check_quiz_images funkciju."""

    @pytest.mark.skip(reason="Requires Docker access")
    def test_check_quiz_images(self):
        """Test funkcije (preskočen bez Docker-a)."""
        # Ova funkcija koristi subprocess i docker
        # Testira se samo import bez stvarnog izvršavanja
        from app.utils import monitor_quiz_images

        assert callable(monitor_quiz_images.check_quiz_images)


class TestCheckAllQuizIssues:
    """Testovi za check_all_quiz_issues funkciju."""

    @pytest.mark.skip(reason="Requires Docker access")
    def test_check_all_quiz_issues(self):
        """Test funkcije (preskočen bez Docker-a)."""
        from app.utils import monitor_quiz_images

        assert callable(monitor_quiz_images.check_all_quiz_issues)


def test_module_imports():
    """Test da se modul može uvoziti."""
    from app.utils import monitor_quiz_images

    assert monitor_quiz_images is not None


def test_check_quiz_images_exists():
    """Test da funkcija postoji."""
    from app.utils.monitor_quiz_images import check_quiz_images

    assert callable(check_quiz_images)


def test_check_all_quiz_issues_exists():
    """Test da funkcija postoji."""
    from app.utils.monitor_quiz_images import check_all_quiz_issues

    assert callable(check_all_quiz_issues)
