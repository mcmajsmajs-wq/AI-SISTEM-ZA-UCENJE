# -*- coding: utf-8 -*-
"""
================================================================================
API INTEGRATION TESTS
================================================================================
Integration testovi za API endpointe.

Pokretanje:
    pytest tests/integration/test_api.py -v
================================================================================
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


class TestHealthEndpoints:
    """Testovi za health check endpointe."""

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test /health endpoint-a."""
        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_live_check(self):
        """Test /live endpoint-a."""
        from app.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/live")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ready_check(self):
        """Test /ready endpoint-a - sa mock database."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=True):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert "database" in data["checks"]

    @pytest.mark.asyncio
    async def test_ready_check_database_unhealthy(self):
        """Test /ready endpoint-a kada je baza nezdrava."""
        from app.main import app

        with patch("app.db.session.check_database_connection", return_value=False):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/ready")

        assert response.status_code == 503


class TestAuthEndpoints:
    """Testovi za autentikacione endpointe."""

    @pytest.mark.asyncio
    async def test_register_success(self, db):
        """Test uspesne registracije."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "password": "TestPassword123!",
                    "full_name": "New User",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, db, test_user):
        """Test registracije sa dupliranim email-om."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": test_user.email,
                    "password": "TestPassword123!",
                    "full_name": "Another User",
                },
            )

        assert response.status_code == 400

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_success(self, db, test_user, test_user_data):
        """Test uspesnog login-a."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={  # Login endpoint koristi Form() parametre (OAuth2)
                    "username": test_user_data["email"],
                    "password": test_user_data["password"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, db, test_user_data):
        """Test login-a sa pogresnim password-om."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                data={  # Login endpoint koristi Form() parametre (OAuth2)
                    "username": test_user_data["email"],
                    "password": "WrongPassword123!",
                },
            )

        assert response.status_code == 401

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_me_success(self, db, test_user, test_user_token):
        """Test /auth/me endpoint-a."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_me_no_token(self, db):
        """Test /auth/me bez token-a."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_token(self, db, test_user, test_refresh_token):
        """Test refresh token endpoint-a."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/refresh", params={"refresh_token": test_refresh_token}
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

        app.dependency_overrides.clear()


class TestUserEndpoints:
    """Testovi za korisnicke endpointe."""

    @pytest.mark.asyncio
    async def test_get_user_me(self, db, test_user, test_user_token):
        """Test GET /users/me."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_user_me(self, db, test_user, test_user_token):
        """Test PUT /users/me."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/users/me",
                headers={"Authorization": f"Bearer {test_user_token}"},
                json={"full_name": "Updated Name", "timezone": "Europe/Belgrade"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_password_success(
        self, db, test_user, test_user_token, test_user_data
    ):
        """Test PUT /users/me/password."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/users/me/password",
                headers={"Authorization": f"Bearer {test_user_token}"},
                params={
                    "current_password": test_user_data["password"],
                    "new_password": "NewPassword123!",
                },
            )

        assert response.status_code == 200

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, db, test_user_token):
        """Test promene password-a sa pogresnim trenutnim password-om."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                "/api/v1/users/me/password",
                headers={"Authorization": f"Bearer {test_user_token}"},
                params={
                    "current_password": "WrongPassword123!",
                    "new_password": "NewPassword123!",
                },
            )

        assert response.status_code == 400

        app.dependency_overrides.clear()


class TestDocumentEndpoints:
    """Testovi za dokument endpointe."""

    @pytest.mark.asyncio
    async def test_list_documents(self, db, test_user, test_user_token, test_document):
        """Test GET /documents."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(
            app=app, base_url="http://test", follow_redirects=True
        ) as client:
            response = await client.get(
                "/api/v1/documents/",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_document_by_id(
        self, db, test_user, test_user_token, test_document
    ):
        """Test GET /documents/{id}."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/documents/{test_document.id}",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_document.id)
        assert data["title"] == test_document.title

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, db, test_user_token):
        """Test GET /documents/{id} sa nepostojecim ID-em."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/api/v1/documents/00000000-0000-0000-0000-000000000000",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 404

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_document_chunks(
        self, db, test_user, test_user_token, test_document, test_chunks
    ):
        """Test GET /documents/{id}/chunks."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/documents/{test_document.id}/chunks",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        # chunks endpoint returns a list directly
        assert isinstance(data, list)
        assert len(data) >= 1

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_chunk(
        self, db, test_user, test_user_token, test_document, test_chunks
    ):
        """Test PUT /documents/{id}/chunks/{chunk_id}."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        chunk = test_chunks[0]

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/api/v1/documents/{test_document.id}/chunks/{chunk.id}",
                headers={"Authorization": f"Bearer {test_user_token}"},
                params={"translated_content": "Izmenjeni prevod teksta."},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "updated"

        app.dependency_overrides.clear()


class TestFileEndpoints:
    """Testovi za file endpointe."""

    @pytest.mark.asyncio
    async def test_list_files(self, db, test_user, test_user_token, test_file):
        """Test GET /files."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(
            app=app, base_url="http://test", follow_redirects=True
        ) as client:
            response = await client.get(
                "/api/v1/files/", headers={"Authorization": f"Bearer {test_user_token}"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_file_by_id(self, db, test_user, test_user_token, test_file):
        """Test GET /files/{id}."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/api/v1/files/{test_file.id}",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_file.id)

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_file(self, db, test_user, test_user_token, test_file):
        """Test DELETE /files/{id}."""
        from app.main import app
        from app.db.session import get_db

        app.dependency_overrides[get_db] = lambda: db

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/api/v1/files/{test_file.id}",
                headers={"Authorization": f"Bearer {test_user_token}"},
            )

        assert response.status_code == 204

        app.dependency_overrides.clear()
