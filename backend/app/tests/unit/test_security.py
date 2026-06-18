# -*- coding: utf-8 -*-
"""
================================================================================
FAZA 8 SECURITY TESTS
================================================================================
Testovi za FAZA 8: API Key Security - Enkripcija i validacija.
Pokretanje:
    pytest app/tests/unit/test_security.py -v
================================================================================
"""

import pytest
from app.services.security import (
    EncryptionService,
    APIKeyValidator,
)


class TestEncryptionService:
    """Testovi za EncryptionService."""

    def test_encrypt_decrypt(self):
        """Test enkripcije i dekripcije."""
        encryption = EncryptionService()
        original = "sk-test-api-key-12345"

        encrypted = encryption.encrypt(original)
        assert encrypted != original
        assert encrypted != ""

        decrypted = encryption.decrypt(encrypted)
        assert decrypted == original

    def test_encrypt_empty(self):
        """Test praznog teksta."""
        encryption = EncryptionService()

        assert encryption.encrypt("") == ""
        assert encryption.decrypt("") == ""

    def test_hash_key(self):
        """Test hashiranja ključa."""
        encryption = EncryptionService()
        api_key = "sk-test-key-12345"

        hash1 = encryption.hash_key(api_key)
        hash2 = encryption.hash_key(api_key)

        assert hash1 == hash2
        assert len(hash1) == 16

    def test_verify_key(self):
        """Test verifikacije ključa."""
        encryption = EncryptionService()
        api_key = "sk-test-key-12345"

        key_hash = encryption.hash_key(api_key)
        assert encryption.verify_key(api_key, key_hash) is True
        assert encryption.verify_key("wrong-key", key_hash) is False


class TestAPIKeyValidator:
    """Testovi za APIKeyValidator."""

    def test_validate_openai_valid(self):
        """Test validnog OpenAI ključa."""
        valid, error = APIKeyValidator.validate("openai", "sk-abcdefghijk1234567890")
        assert valid is True
        assert error is None

    def test_validate_openai_invalid(self):
        """Test nevalidnog OpenAI ključa."""
        valid, error = APIKeyValidator.validate("openai", "invalid-key")
        assert valid is False
        assert error is not None

    def test_validate_claude_valid(self):
        """Test validnog Claude ključa."""
        valid, error = APIKeyValidator.validate(
            "claude", "sk-ant-api03-abcdefghijk123456789012345678901234567890"
        )
        assert valid is True
        assert error is None

    def test_validate_groq_valid(self):
        """Test validnog Groq ključa."""
        valid, error = APIKeyValidator.validate(
            "groq", "gsk_abcdefghijk123456789012345678901234567890"
        )
        assert valid is True
        assert error is None

    def test_validate_ollama(self):
        """Test Ollama (ne zahteva ključ)."""
        valid, error = APIKeyValidator.validate("ollama", "")
        assert valid is True
        assert error is None

        valid, error = APIKeyValidator.validate("ollama", "localhost:11434")
        assert valid is True

    def test_validate_unknown_provider(self):
        """Test nepoznatog provajdera."""
        valid, error = APIKeyValidator.validate("unknown", "some-key")
        assert valid is False

    def test_get_supported_providers(self):
        """Test liste podržanih provajdera."""
        providers = APIKeyValidator.get_supported_providers()
        assert "openai" in providers
        assert "claude" in providers
        assert "gemini" in providers
        assert "ollama" in providers

    def test_validate_model(self):
        """Test validacije modela."""
        valid, error = APIKeyValidator.validate_model("openai", "gpt-4")
        assert valid is True

        valid, error = APIKeyValidator.validate_model("openai", "unknown-model")
        assert valid is False

    def test_get_provider_models(self):
        """Test liste modela."""
        models = APIKeyValidator.get_provider_models("openai")
        assert "gpt-4" in models
        assert "gpt-4o" in models

    def test_get_provider_info(self):
        """Test informacija o provajderu."""
        info = APIKeyValidator.get_provider_info("openai")
        assert info["provider"] == "openai"
        assert "models" in info
        assert info["requires_key"] is True

    def test_ollama_requires_no_key(self):
        """Test da Ollama ne zahteva ključ."""
        info = APIKeyValidator.get_provider_info("ollama")
        assert info["requires_key"] is False


class TestValidatorsEdgeCases:
    """Testovi za granične slučajeve."""

    def test_empty_api_key(self):
        """Test praznog API ključa."""
        valid, error = APIKeyValidator.validate("openai", "")
        assert valid is False

    def test_empty_provider(self):
        """Test praznog provajdera."""
        valid, error = APIKeyValidator.validate("", "some-key")
        assert valid is False


class TestEncryptionEdgeCases:
    """Testovi za granične slučajeve enkripcije."""

    def test_encrypt_unicode(self):
        """Test unicode karaktera."""
        encryption = EncryptionService()
        original = "ključ саћирлица ćirilic"

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original

    def test_encrypt_long_text(self):
        """Test dugog teksta."""
        encryption = EncryptionService()
        original = "sk-" + "a" * 200

        encrypted = encryption.encrypt(original)
        decrypted = encryption.decrypt(encrypted)

        assert decrypted == original


class TestKeyManagerImport:
    """Testovi za KeyManager import."""

    def test_import_key_manager(self):
        """Test importa KeyManager."""
        from app.services.security import KeyManager

        km = KeyManager()
        assert km is not None
        assert km.encryption is not None

    def test_import_validators(self):
        """Test importa validators."""
        from app.services.security import APIKeyValidator

        assert APIKeyValidator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
