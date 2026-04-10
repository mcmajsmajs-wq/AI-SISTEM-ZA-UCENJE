# -*- coding: utf-8 -*-
"""
================================================================================
MONITORING UTILS TESTS
================================================================================
Unit testovi za utils/monitoring.py.

Pokretanje:
    pytest tests/unit/test_monitoring_utils.py -v
================================================================================
"""

import pytest
from datetime import datetime

from app.utils.monitoring import ActionLogger


class TestActionLogger:
    """Testovi za ActionLogger klasu."""

    @pytest.fixture
    def logger(self):
        """ActionLogger instanca."""
        return ActionLogger()

    def test_init(self, logger):
        """Test inicijalizacije."""
        assert logger.actions == []
        assert logger.errors == []

    def test_log_action_success(self, logger):
        """Test beleženja uspešne akcije."""
        logger.log_action("test_action", {"key": "value"}, "success")

        assert len(logger.actions) == 1
        assert logger.actions[0]["type"] == "test_action"
        assert logger.actions[0]["status"] == "success"

    def test_log_action_error(self, logger):
        """Test beleženja greške."""
        logger.log_action("error_action", {"error": "message"}, "error")

        assert len(logger.actions) == 1
        assert len(logger.errors) == 1
        assert logger.errors[0]["status"] == "error"

    def test_log_action_adds_timestamp(self, logger):
        """Test da dodaje timestamp."""
        logger.log_action("action", {}, "success")

        assert "timestamp" in logger.actions[0]
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(logger.actions[0]["timestamp"])

    def test_log_action_stores_details(self, logger):
        """Test da čuva details."""
        details = {"user": "test_user", "action": "login"}
        logger.log_action("login", details, "success")

        assert logger.actions[0]["details"] == details

    def test_multiple_actions(self, logger):
        """Test više akcija."""
        logger.log_action("action1", {}, "success")
        logger.log_action("action2", {}, "success")
        logger.log_action("action3", {}, "error")

        assert len(logger.actions) == 3
        assert len(logger.errors) == 1

    def test_get_actions(self, logger):
        """Test get_actions metode."""
        logger.log_action("action1", {}, "success")
        logger.log_action("action2", {}, "success")

        actions = logger.get_actions()
        assert len(actions) == 2

    def test_get_errors(self, logger):
        """Test get_errors metode."""
        logger.log_action("ok", {}, "success")
        logger.log_action("error1", {}, "error")
        logger.log_action("error2", {}, "error")

        errors = logger.get_errors()
        assert len(errors) == 2

    def test_log_error(self, logger):
        """Test log_error metode."""
        logger.log_error("Error message", {"detail": "something failed"})

        assert len(logger.errors) == 1
        assert logger.errors[0]["type"] == "Error message"

    def test_clear(self, logger):
        """Test clear metode."""
        logger.log_action("action", {}, "success")
        logger.log_error("error", {})

        logger.clear()

        assert logger.actions == []
        assert logger.errors == []
