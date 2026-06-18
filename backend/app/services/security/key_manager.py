# -*- coding: utf-8 -*-
"""
================================================================================
KEY MANAGER SERVICE
================================================================================
FAZA 8: Upravljanje korisničkim API ključevima.

Servis za čuvanje, dobijanje i brisanje korisničkih API ključeva.
Enkriptuje ključeve pre čuvanja u bazu i dekriptuje pri dobijanju.

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-09
================================================================================
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.services.security.encryption import EncryptionService
from app.services.security.validators import APIKeyValidator


class KeyManager:
    """Upravljanje korisničkim API ključevima.

    Attributes:
        encryption: EncryptionService instanca
    """

    def __init__(self):
        self.encryption = EncryptionService()

    def store_key(self, db: Session, user_id: int, provider: str, api_key: str) -> dict:
        """Čuva enkriptovani API key za korisnika.

        Args:
            db: Database session
            user_id: ID korisnika
            provider: Ime provajdera (openai, claude, itd.)
            api_key: API ključ za čuvanje

        Returns:
            Dict sa rezultatom ili greškom
        """
        valid, error = APIKeyValidator.validate(provider, api_key)
        if not valid:
            return {"status": "error", "message": error}

        encrypted = self.encryption.encrypt(api_key)
        key_hash = self.encryption.hash_key(api_key)

        from app.db.models.user import UserAPIKey

        existing = (
            db.query(UserAPIKey).filter_by(user_id=user_id, provider=provider).first()
        )

        if existing:
            existing.encrypted_key = encrypted
            existing.key_hash = key_hash
            existing.is_active = True
            existing.updated_at = datetime.utcnow()
            db.commit()
            return {
                "status": "updated",
                "provider": provider,
                "message": f"API ključ za {provider} ažuriran",
            }

        new_key = UserAPIKey(
            user_id=user_id,
            provider=provider,
            encrypted_key=encrypted,
            key_hash=key_hash,
            is_active=True,
        )
        db.add(new_key)
        db.commit()

        return {
            "status": "created",
            "provider": provider,
            "message": f"API ključ za {provider} sačuvan",
        }

    def get_key(self, db: Session, user_id: int, provider: str) -> Optional[str]:
        """Dekriptuje i vraća API key.

        Args:
            db: Database session
            user_id: ID korisnika
            provider: Ime provajdera

        Returns:
            Dekriptovani API ključ ili None
        """
        from app.db.models.user import UserAPIKey

        key_obj = (
            db.query(UserAPIKey)
            .filter_by(user_id=user_id, provider=provider, is_active=True)
            .first()
        )

        if not key_obj:
            return None

        return self.encryption.decrypt(key_obj.encrypted_key)

    def get_all_keys(self, db: Session, user_id: int) -> dict:
        """Vraća sve API ključeve za korisnika (bez dekripcije).

        Args:
            db: Database session
            user_id: ID korisnika

        Returns:
            Dict sa dostupnim provajderima
        """
        from app.db.models.user import UserAPIKey

        keys = db.query(UserAPIKey).filter_by(user_id=user_id, is_active=True).all()

        providers = [k.provider for k in keys]
        return {"status": "ok", "providers": providers, "count": len(providers)}

    def delete_key(self, db: Session, user_id: int, provider: str) -> dict:
        """Briše (deaktivira) API key.

        Args:
            db: Database session
            user_id: ID korisnika
            provider: Ime provajdera

        Returns:
            Dict sa rezultatom
        """
        from app.db.models.user import UserAPIKey

        key_obj = (
            db.query(UserAPIKey).filter_by(user_id=user_id, provider=provider).first()
        )

        if key_obj:
            key_obj.is_active = False
            key_obj.deleted_at = datetime.utcnow()
            db.commit()
            return {
                "status": "deleted",
                "provider": provider,
                "message": f"API ključ za {provider} obrisan",
            }

        return {
            "status": "not_found",
            "provider": provider,
            "message": f"API ključ za {provider} nije pronađen",
        }

    def has_key(self, db: Session, user_id: int, provider: str) -> bool:
        """Proverava da li korisnik ima API key za provajdera.

        Args:
            db: Database session
            user_id: ID korisnika
            provider: Ime provajdera

        Returns:
            True ako postoji
        """
        from app.db.models.user import UserAPIKey

        return (
            db.query(UserAPIKey)
            .filter_by(user_id=user_id, provider=provider, is_active=True)
            .first()
            is not None
        )

    def get_or_use_key(
        self,
        db: Session,
        user_id: int,
        provider: str,
        provided_key: Optional[str] = None,
    ) -> Optional[str]:
        """Vraća API key koristeći pruženi ili sačuvani.

        Priority:
        1. provided_key (ako je dat)
        2. Sačuvani key iz baze

        Args:
            db: Database session
            user_id: ID korisnika
            provider: Ime provajdera
            provided_key: Priloženi API ključ

        Returns:
            API ključ ili None
        """
        if provided_key:
            return provided_key

        return self.get_key(db, user_id, provider)


class KeyManagerService(KeyManager):
    """Alias za KeyManager (backward compatibility)."""
