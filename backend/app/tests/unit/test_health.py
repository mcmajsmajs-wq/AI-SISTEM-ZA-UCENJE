# -*- coding: utf-8 -*-
"""
================================================================================
HEALTH ENDPOINT TESTOVI
================================================================================
Unit testovi za health endpoint-e.

Verzija: 1.0.0
================================================================================
"""

import pytest

from app.api.endpoints.health import health_check, readiness_check, liveness_check


class TestHealthEndpoints:
    """
    Testovi za /health endpoint.
    """

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self):
        """
        Testira da health_check vraća dict.
        """
        result = await health_check()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy_status(self):
        """
        Testira da health_check vraća healthy status.
        """
        result = await health_check()
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_returns_timestamp(self):
        """
        Testira da health_check vraća timestamp.
        """
        result = await health_check()
        assert "timestamp" in result
        assert result["timestamp"] is not None

    @pytest.mark.asyncio
    async def test_health_check_returns_version(self):
        """
        Testira da health_check vraća verziju.
        """
        result = await health_check()
        assert "version" in result
        assert result["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_health_check_returns_python_version(self):
        """
        Testira da health_check vraća Python verziju.
        """
        result = await health_check()
        assert "python_version" in result

    @pytest.mark.asyncio
    async def test_health_check_returns_platform(self):
        """
        Testira da health_check vraća platformu.
        """
        result = await health_check()
        assert "platform" in result


class TestLivenessEndpoints:
    """
    Testovi za /live endpoint.
    """

    @pytest.mark.asyncio
    async def test_liveness_check_returns_200(self):
        """
        Testira da liveness_check vraća dict.
        """
        result = await liveness_check()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_liveness_check_returns_alive_status(self):
        """
        Testira da liveness_check vraća alive status.
        """
        result = await liveness_check()
        assert result["status"] == "alive"

    @pytest.mark.asyncio
    async def test_liveness_check_returns_timestamp(self):
        """
        Testira da liveness_check vraća timestamp.
        """
        result = await liveness_check()
        assert "timestamp" in result


class TestReadinessEndpoints:
    """
    Testovi za /ready endpoint.
    """

    @pytest.mark.asyncio
    async def test_readiness_check_returns_200(self):
        """
        Testira da readiness_check vraća dict.
        """
        result = await readiness_check()
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_readiness_check_returns_ready_status(self):
        """
        Testira da readiness_check vraća ready status.
        """
        result = await readiness_check()
        assert result["status"] == "ready"

    @pytest.mark.asyncio
    async def test_readiness_check_returns_timestamp(self):
        """
        Testira da readiness_check vraća timestamp.
        """
        result = await readiness_check()
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_readiness_check_returns_checks(self):
        """
        Testira da readiness_check vraća checks dict.
        """
        result = await readiness_check()
        assert "checks" in result
        assert isinstance(result["checks"], dict)


class TestHealthResponseFormat:
    """
    Testovi za format odgovora.
    """

    @pytest.mark.asyncio
    async def test_health_response_is_json(self):
        """
        Testira da health response može biti serializovan u JSON.
        """
        result = await health_check()
        import json

        json.dumps(result)

    @pytest.mark.asyncio
    async def test_health_response_has_required_fields(self):
        """
        Testira da health response ima sva potrebna polja.
        """
        result = await health_check()
        required_fields = [
            "status",
            "timestamp",
            "version",
            "python_version",
            "platform",
        ]
        for field in required_fields:
            assert field in result

    @pytest.mark.asyncio
    async def test_health_status_is_string(self):
        """
        Testira da je status string.
        """
        result = await health_check()
        assert isinstance(result["status"], str)
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_liveness_response_is_json(self):
        """
        Testira da liveness response može biti serializovan u JSON.
        """
        result = await liveness_check()
        import json

        json.dumps(result)

    @pytest.mark.asyncio
    async def test_readiness_response_is_json(self):
        """
        Testira da readiness response može biti serializovan u JSON.
        """
        result = await readiness_check()
        import json

        json.dumps(result)
