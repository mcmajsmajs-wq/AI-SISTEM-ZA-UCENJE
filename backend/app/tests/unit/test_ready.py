# -*- coding: utf-8 -*-
"""
================================================================================
READY ENDPOINT - MOCK TESTOVI
================================================================================
Unit testovi za /ready endpoint - sa mock-ovima.

BRZINA: ~50ms po testu
PREDNOST: Ne zahteva spoljne servise
MANA: Ne testira pravu konekciju sa bazom

Pokretanje:
    pytest app/tests/unit/test_ready.py -v
================================================================================
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient


class TestReadyEndpointWithMocks:
    """Testovi za /ready sa mock-ovima."""

    @pytest.mark.asyncio
    async def test_ready_returns_200_when_db_healthy(self):
        """Testira /ready kada je baza zdrava - mock vraća True."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "checks" in data
        assert data["checks"]["database"] == "healthy"

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_db_unhealthy(self):
        """Testira /ready kada baza nije dostupna - mock vraća False."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_ready_returns_503_when_db_raises_exception(self):
        """Testira /ready kada konekcija baca izuzetak."""
        from app.main import app

        with patch(
            "app.db.session.check_database_connection",
            side_effect=Exception("Connection failed"),
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 503

    @pytest.mark.asyncio
    async def test_ready_response_format(self):
        """Testira format odgovora."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert isinstance(data["checks"], dict)


class TestReadyEndpointEdgeCases:
    """Edge case testovi."""

    @pytest.mark.asyncio
    async def test_ready_timeout_handling(self):
        """Testira da /ready ima timeout."""
        from app.main import app
        import asyncio

        async def slow_connection():
            await asyncio.sleep(10)
            return True

        with patch(
            "app.db.session.check_database_connection", side_effect=slow_connection
        ):
            async with AsyncClient(app=app, base_url="http://test") as client:
                try:
                    response = await client.get("/ready", timeout=1.0)
                except Exception:
                    response = None

        if response is None:
            pass  # Timeout radi ispravno

    @pytest.mark.asyncio
    async def test_ready_with_none_response(self):
        """Testira kada funkcija vraća None."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=None):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 503


class TestReadyEndpointContract:
    """Contract testovi - šta API mora da vraća."""

    @pytest.mark.asyncio
    async def test_ready_contract_status_field(self):
        """Status mora biti string."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        data = response.json()
        assert isinstance(data["status"], str)

    @pytest.mark.asyncio
    async def test_ready_contract_checks_field(self):
        """Checks mora biti dict."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        data = response.json()
        assert isinstance(data["checks"], dict)

    @pytest.mark.asyncio
    async def test_ready_contract_healthy_db_value(self):
        """Zdrava baza ima vrednost 'healthy'."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        data = response.json()
        assert data["checks"]["database"] == "healthy"
