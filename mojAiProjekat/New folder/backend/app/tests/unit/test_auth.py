# -*- coding: utf-8 -*-
"""
================================================================================
AUTH SERVICE TESTS
================================================================================
Unit testovi za AuthService - autentikacija, JWT tokeni, password hashing.

Pokretanje:
    pytest tests/unit/test_auth.py -v
    pytest tests/unit/test_auth.py --cov=app.services.auth
================================================================================
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.auth import AuthService, get_current_user
from app.db.models.user import User


class TestPasswordHashing:
    """Testovi za password hashing funkcionalnosti."""
    
    def test_get_password_hash(self):
        """Test da li se password hashuje ispravno."""
        password = "TestPassword123!"
        hashed = AuthService.get_password_hash(password)
        
        assert hashed != password
        assert hashed.startswith("$2b$")  # bcrypt prefix
        assert len(hashed) > 50
    
    def test_verify_password_correct(self):
        """Test verifikacije ispravnog password-a."""
        password = "TestPassword123!"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifikacije neispravnog password-a."""
        password = "TestPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = AuthService.get_password_hash(password)
        
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_different_passwords_different_hashes(self):
        """Test da različiti password-i daju različite hasheve."""
        password1 = "Password123!"
        password2 = "Password456!"
        
        hash1 = AuthService.get_password_hash(password1)
        hash2 = AuthService.get_password_hash(password2)
        
        assert hash1 != hash2
    
    def test_same_password_different_hashes(self):
        """Test da isti password daje različite hasheve (zbog salt-a)."""
        password = "SamePassword123!"
        
        hash1 = AuthService.get_password_hash(password)
        hash2 = AuthService.get_password_hash(password)
        
        assert hash1 != hash2
        assert AuthService.verify_password(password, hash1)
        assert AuthService.verify_password(password, hash2)


class TestJWTToken:
    """Testovi za JWT token generisanje i validaciju."""
    
    def test_create_access_token(self):
        """Test kreiranja access token-a."""
        data = {"sub": "123"}
        token = AuthService.create_access_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_create_refresh_token(self):
        """Test kreiranja refresh token-a."""
        data = {"sub": "123"}
        token = AuthService.create_refresh_token(data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_decode_access_token(self):
        """Test dekodiranja access token-a."""
        data = {"sub": "123", "email": "test@example.com"}
        token = AuthService.create_access_token(data)
        
        payload = AuthService.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["email"] == "test@example.com"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_decode_refresh_token(self):
        """Test dekodiranja refresh token-a."""
        data = {"sub": "123"}
        token = AuthService.create_refresh_token(data)
        
        payload = AuthService.decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "refresh"
    
    def test_decode_invalid_token(self):
        """Test dekodiranja neispravnog token-a."""
        invalid_token = "invalid.token.here"
        
        payload = AuthService.decode_token(invalid_token)
        
        assert payload is None
    
    def test_decode_expired_token(self):
        """Test dekodiranja isteklog token-a."""
        data = {"sub": "123"}
        expired_delta = timedelta(seconds=-1)
        token = AuthService.create_access_token(data, expired_delta)
        
        payload = AuthService.decode_token(token)
        
        assert payload is None
    
    def test_token_custom_expiration(self):
        """Test custom expiration time-a za token."""
        data = {"sub": "123"}
        custom_delta = timedelta(hours=2)
        
        token = AuthService.create_access_token(data, custom_delta)
        payload = AuthService.decode_token(token)
        
        assert payload is not None
        
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        expected_exp = datetime.utcnow() + custom_delta
        
        assert abs((exp_time - expected_exp).total_seconds()) < 5


class TestUserOperations:
    """Testovi za korisnicke operacije."""
    
    def test_get_user_by_email(self, db, test_user):
        """Test dohvatanja korisnika po email-u."""
        user = AuthService.get_user_by_email(db, test_user.email)
        
        assert user is not None
        assert user.email == test_user.email
        assert user.id == test_user.id
    
    def test_get_user_by_email_not_found(self, db):
        """Test dohvatanja nepostojeceg korisnika."""
        user = AuthService.get_user_by_email(db, "nonexistent@example.com")
        
        assert user is None
    
    def test_get_user_by_id(self, db, test_user):
        """Test dohvatanja korisnika po ID-u."""
        user = AuthService.get_user_by_id(db, str(test_user.id))
        
        assert user is not None
        assert user.id == test_user.id
    
    def test_get_user_by_id_not_found(self, db):
        """Test dohvatanja korisnika sa nepostojecim ID-em."""
        user = AuthService.get_user_by_id(db, "99999")
        
        assert user is None
    
    def test_authenticate_user_success(self, db, test_user, test_user_data):
        """Test uspesne autentikacije korisnika."""
        user = AuthService.authenticate_user(
            db, 
            test_user_data["email"],
            test_user_data["password"]
        )
        
        assert user is not None
        assert user.email == test_user.email
    
    def test_authenticate_user_wrong_password(self, db, test_user, test_user_data):
        """Test autentikacije sa pogresnim password-om."""
        user = AuthService.authenticate_user(
            db,
            test_user_data["email"],
            "WrongPassword123!"
        )
        
        assert user is None
    
    def test_authenticate_user_nonexistent_email(self, db):
        """Test autentikacije sa nepostojecim email-om."""
        user = AuthService.authenticate_user(
            db,
            "nonexistent@example.com",
            "SomePassword123!"
        )
        
        assert user is None
    
    def test_authenticate_user_inactive(self, db, test_user_data):
        """Test autentikacije neaktivnog korisnika."""
        from app.services.auth import AuthService
        
        hashed_password = AuthService.get_password_hash(test_user_data["password"])
        inactive_user = User(
            email="inactive@example.com",
            hashed_password=hashed_password,
            full_name="Inactive User",
            is_active=False,
            is_verified=False
        )
        db.add(inactive_user)
        db.commit()
        
        user = AuthService.authenticate_user(
            db,
            "inactive@example.com",
            test_user_data["password"]
        )
        
        assert user is None


class TestCreateUser:
    """Testovi za kreiranje korisnika."""
    
    def test_create_user_success(self, db):
        """Test uspesnog kreiranja korisnika."""
        user = AuthService.create_user(
            db,
            email="newuser@example.com",
            password="NewPassword123!",
            full_name="New User"
        )
        
        assert user is not None
        assert user.email == "newuser@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
        assert user.is_verified is False
        assert AuthService.verify_password("NewPassword123!", user.hashed_password)
    
    def test_create_user_duplicate_email(self, db, test_user):
        """Test kreiranja korisnika sa dupliranim email-om."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            AuthService.create_user(
                db,
                email=test_user.email,
                password="AnotherPassword123!",
                full_name="Another User"
            )
        
        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail.lower()


class TestGetCurrentUser:
    """Testovi za get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_success(self, db, test_user, test_user_token):
        """Test dohvatanja trenutnog korisnika sa validnim tokenom."""
        from fastapi import Depends
        from app.services.auth import oauth2_scheme
        
        mock_token = test_user_token
        
        user = await get_current_user(token=mock_token, db=db)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.email == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, db):
        """Test sa neispravnim tokenom."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="invalid.token", db=db)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_user_refresh_token_instead_of_access(self, db, test_refresh_token):
        """Test sa refresh token-om umesto access token-a."""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=test_refresh_token, db=db)
        
        assert exc_info.value.status_code == 401


class TestPasswordStrength:
    """Testovi za jacinu password-a."""
    
    def test_hash_performance(self):
        """Test da hashing nije previse spor (bcrypt je namerno spor)."""
        import time
        
        password = "TestPassword123!"
        
        start = time.time()
        AuthService.get_password_hash(password)
        elapsed = time.time() - start
        
        assert elapsed < 2.0
    
    def test_long_password(self):
        """Test sa vrlo dugim password-om."""
        long_password = "A" * 1000
        
        hashed = AuthService.get_password_hash(long_password)
        
        assert AuthService.verify_password(long_password, hashed)
    
    def test_unicode_password(self):
        """Test sa Unicode karakterima u password-u."""
        unicode_password = "Парола123!测试"
        
        hashed = AuthService.get_password_hash(unicode_password)
        
        assert AuthService.verify_password(unicode_password, hashed)
    
    def test_empty_password_handling(self):
        """Test da prazan password ne pravi probleme."""
        empty_password = ""
        
        hashed = AuthService.get_password_hash(empty_password)
        
        assert AuthService.verify_password(empty_password, hashed)
