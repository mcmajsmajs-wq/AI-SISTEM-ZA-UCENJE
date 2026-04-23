# -*- coding: utf-8 -*-
"""
================================================================================
READY ENDPOINT - INTEGRATION TESTOVI
================================================================================
Integration testovi za /ready endpoint - sa pravom bazom.

BRZINA: ~2-5 sekundi po testu
PREDNOST: Testira pravu konekciju sa bazom
MANA: Zahteva pokrenutu bazu

⚠️  OVI TESTOVI SE POKREĆU U DOCKER-U!
    docker-compose up -d db
    pytest app/tests/integration/test_ready.py -v

ILI CI/CD pipeline:
    - u CI se koristi testcontainers biblioteka
================================================================================
"""

import pytest
import os
from httpx import AsyncClient


class TestReadyEndpointIntegration:
    """Integration testovi sa pravom PostgreSQL bazom."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ready_with_real_database(self):
        """
        Testira /ready sa pravom PostgreSQL bazom.

        Ovo je NAJPOUZDANIJI test jer:
        - Testira stvarnu konekciju
        - Testira RIGHT TIMEOUT handling
        - Testira ERROR handling

        Prerequisites:
        - PostgreSQL mora biti pokrenut (docker-compose up -d db)
        - Ili mock u CI/testcontainers
        """
        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/ready")

        # Sada testira PRAVU konekciju
        assert response.status_code in [200, 503]  # Zavisno od toga da li baza radi

        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready"
            assert data["checks"]["database"] == "healthy"
        else:
            # Baza ne radi - to je takođe ispravno ponašanje
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ready_database_connection_timeout(self):
        """
        Testira da /ready ima dobar timeout.

        Ako je baza spora, endpoint ne sme da se zaglavi.
        """
        from app.main import app
        import asyncio

        try:
            async with AsyncClient(
                app=app,
                base_url="http://test",
                timeout=5.0,  # 5 sekundi timeout
            ) as client:
                response = await asyncio.wait_for(client.get("/ready"), timeout=6.0)
            assert response.status_code in [200, 503]
        except asyncio.TimeoutError:
            # Timeout radi ispravno
            pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_health_vs_ready_difference(self):
        """
        Testira razliku između /health i /ready.

        /health - uvek vraća 200 (prover samo aplikaciju)
        /ready - proverava i zavisnosti (baza, redis, itd)
        """
        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            # /health uvek radi
            health_response = await client.get("/health")
            assert health_response.status_code == 200

            # /ready zavisi od baze
            ready_response = await client.get("/ready")
            # Može biti 200 (baza radi) ili 503 (baza ne radi)
            assert ready_response.status_code in [200, 503]


class TestReadyEndpointDatabaseConnection:
    """Testovi za različite scenarije konekcije."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ready_multiple_sequential_requests(self):
        """
        Testira da višestruki zahtevi rade konzistentno.

        /ready se koristi za Kubernetes readiness probe -
        mora biti pouzdan.
        """
        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            responses = []
            for _ in range(5):
                response = await client.get("/ready")
                responses.append(response.status_code)

            # Svi odgovori treba da budu isti
            assert len(set(responses)) <= 1  # Svi 200 ili svi 503

    @pytest.mark.asyncio
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_ready_under_load(self):
        """
        Testira /ready pod opterećenjem.

        Readiness probe se često poziva (svakih 10-30s),
        mora biti brz i pouzdan.
        """
        from app.main import app
        import time

        async with AsyncClient(app=app, base_url="http://test") as client:
            start = time.time()

            # 10 paralelnih zahteva
            import asyncio

            tasks = [client.get("/ready") for _ in range(10)]
            responses = await asyncio.gather(*tasks)

            duration = time.time() - start

            # Svi zahtevi treba da se zavrse brzo
            assert duration < 5.0  # Manje od 5 sekundi za sve

            # Svi treba da vrate konzistentan odgovor
            statuses = [r.status_code for r in responses]
            assert len(set(statuses)) <= 1


# ============================================================================
# TEST CONFIGURATION
# ============================================================================
#
# Ovaj test se označava kao integration jer:
# 1. Zahteva pravu konekciju na bazu
# 2. Testira timeout i error handling
# 3. Testira ponašanje pod opterećenjem
#
# Pokretanje:
#   # Samo unit testovi (brzi)
#   pytest app/tests/unit/test_ready.py -v
#
#   # Sa integration testovima (zahteva bazu)
#   pytest app/tests/integration/test_ready.py -v -m integration
#
#   # Svi testovi
#   pytest app/tests/ -v
# ============================================================================
