# -*- coding: utf-8 -*-
"""
================================================================================
ENCRYPTION SERVICE
================================================================================
FAZA 8: AES-256-Fernet enkripcija za API ključeve.

Koristi Fernet (symmetric encryption) iz cryptography biblioteke za enkripciju
korisničkih API ključeva. Fernet koristi AES-256 u CBC modu sa PKCS7 paddingom
i HMAC-SHA256 za autentikaciju.

Reference:
- https://cryptography.io/en/latestFernet/
- https://docs.python.org/3/library/hashlib.html

Autor: AI Learning System
Verzija: 1.0
Datum: 2026-04-09
================================================================================
"""

import base64
import hashlib
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class EncryptionService:
    """AES-256-Fernet enkripcija za API ključeve.

    Koristi PBKDF2 za derivaciju ključa iz lozinke i Fernet za simetričnu
    enkripciju. Svaki korisnik ima jedinstveni salt za generisanje ključa.

    Attributes:
        _cipher: Fernet cipher instanca
        _salt: Salt za KDF
    """

    DEFAULT_SALT = b"ai-learning-secure-salt-v1"

    def __init__(
        self, encryption_key: Optional[str] = None, salt: Optional[bytes] = None
    ):
        """Inicijalizuje enkripciju sa datim ključem ili podrazumevanim.

        Args:
            encryption_key: Master ključ za enkripciju (iz settings.ENCRYPTION_KEY)
            salt: Salt za KDF (opciono, za testiranje)
        """
        self._salt = salt or self.DEFAULT_SALT
        self._cipher = self._create_cipher(encryption_key)

    def _create_cipher(self, key: Optional[str]) -> Fernet:
        """Kreira Fernet cipher instancu iz master ključa.

        Args:
            key: Master enkripcijski ključ

        Returns:
            Fernet cipher instanca
        """
        if key is None:
            key = os.environ.get("ENCRYPTION_KEY", "ai-learning-default-key-change-me")

        key_bytes = key.encode() if isinstance(key, str) else key

        if len(key_bytes) < 32:
            key_bytes = hashlib.sha256(key_bytes).digest()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=480000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))

        return Fernet(derived_key)

    def encrypt(self, plaintext: str) -> str:
        """Enkriptuje tekst.

        Args:
            plaintext: Tekst za enkripciju

        Returns:
            Enkriptovani tekst kao base64 string
        """
        if not plaintext:
            return ""

        encrypted = self._cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Dekriptuje tekst.

        Args:
            ciphertext: Enkriptovani tekst

        Returns:
            Dekriptovani plaintext
        """
        if not ciphertext:
            return ""

        try:
            encrypted = base64.urlsafe_b64decode(ciphertext.encode())
            decrypted = self._cipher.decrypt(encrypted)
            return decrypted.decode()
        except Exception as e:
            raise ValueError(f"Dekripcija neuspešna: {e}")

    def hash_key(self, api_key: str) -> str:
        """Kreira hash API ključa za verifikaciju bez čuvanja originala.

        Koristi SHA-256 za kreiranje hash-a. Hash se koristi za verifikaciju
        da li je key ispravan bez potrebe za dekripcijom.

        Args:
            api_key: API ključ za hashiranje

        Returns:
            Hex string prvih 16 karaktera hash-a
        """
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]

    def verify_key(self, api_key: str, key_hash: str) -> bool:
        """Verifikuje da li se API ključ podudatra sa hash-om.

        Args:
            api_key: API ključ za verifikaciju
            key_hash: Sačuvani hash

        Returns:
            True ako se podudaru
        """
        return self.hash_key(api_key) == key_hash

    def generate_key(self) -> str:
        """Generiše novi enkripcijski ključ.

        Returns:
            Novi master ključ kao base64 string
        """
        return base64.urlsafe_b64encode(os.urandom(32)).decode()


class MultiTenantEncryptionService(EncryptionService):
    """Proširena enkripcija za multi-tenant sistem.

    Omogućava različite salt-ove za različite korisnike/tenante.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        super().__init__(encryption_key)

    def create_user_cipher(self, user_id: int) -> Fernet:
        """Kreira cipher sa jedinstvenim salt-om za korisnika.

        Args:
            user_id: ID korisnika

        Returns:
            Fernet cipher sa korisničkim salt-om
        """
        user_salt = hashlib.sha256(str(user_id).encode() + self.DEFAULT_SALT).digest()[
            :16
        ]

        return self._create_cipher_with_salt(user_salt)

    def _create_cipher_with_salt(self, salt: bytes) -> Fernet:
        """Kreira cipher sa datim salt-om.

        Args:
            salt: Salt za KDF

        Returns:
            Fernet cipher
        """
        key = os.environ.get("ENCRYPTION_KEY", "ai-learning-default-key-change-me")
        key_bytes = key.encode()

        if len(key_bytes) < 32:
            key_bytes = hashlib.sha256(key_bytes).digest()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))

        return Fernet(derived_key)
