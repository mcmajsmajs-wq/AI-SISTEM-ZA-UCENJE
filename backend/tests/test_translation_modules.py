# -*- coding: utf-8 -*-
"""
================================================================================
TEST TRANSLATION MODULES - FAZA 5 Verification
================================================================================

Testovi za verifikaciju Translation modularizacije:
- clients/base.py
- clients/ollama.py, deepl.py, openai.py, google.py, claude.py
- providers.py
- Glavni translation.py

Verzija: 1.0.0
================================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestTranslationProviderEnum:
    """Testovi za TranslationProvider enum."""

    def test_provider_enum_exists(self):
        """Test da TranslationProvider enum postoji."""
        from app.services.translation.providers import TranslationProvider

        assert TranslationProvider is not None

    def test_all_providers_defined(self):
        """Test da su svi provideri definisani."""
        from app.services.translation.providers import TranslationProvider

        expected = [
            "ollama",
            "deepl",
            "openai",
            "google",
            "claude",
            "deepseek",
            "libretranslate",
        ]
        actual = [p.value for p in TranslationProvider]

        for e in expected:
            assert e in actual, f"Missing provider: {e}"

    def test_provider_values_are_strings(self):
        """Test da su sve vrednosti stringovi."""
        from app.services.translation.providers import TranslationProvider

        for p in TranslationProvider:
            assert isinstance(p.value, str)


class TestTranslationResult:
    """Testovi za TranslationResult dataclass."""

    def test_translation_result_creation(self):
        """Test kreiranja TranslationResult."""
        from app.services.translation.clients.base import TranslationResult

        result = TranslationResult(
            success=True,
            translated_text="Translated text",
            source_language="en",
            target_language="sr",
            provider="deepl",
            tokens_used=100,
            cost=0.05,
            error=None,
            duration_ms=500.0,
        )

        assert result.success is True
        assert result.translated_text == "Translated text"
        assert result.source_language == "en"
        assert result.target_language == "sr"
        assert result.provider == "deepl"
        assert result.tokens_used == 100
        assert result.cost == 0.05
        assert result.error is None
        assert result.duration_ms == 500.0

    def test_translation_result_failure(self):
        """Test neuspešnog prevoda."""
        from app.services.translation.clients.base import TranslationResult

        result = TranslationResult(success=False, error="API error")

        assert result.success is False
        assert result.error == "API error"


class TestBaseTranslationClient:
    """Testovi za BaseTranslationClient abstract class."""

    def test_base_class_is_abstract(self):
        """Test da je BaseTranslationClient apstraktna klasa."""
        from app.services.translation.clients.base import BaseTranslationClient
        from abc import ABC

        assert issubclass(BaseTranslationClient, ABC)

    def test_base_class_has_abstract_methods(self):
        """Test da BaseTranslationClient ima apstraktne metode."""
        from app.services.translation.clients.base import BaseTranslationClient

        # Provera da klasa ima apstraktne metode
        assert hasattr(BaseTranslationClient, "translate")
        assert hasattr(BaseTranslationClient, "is_available")
        assert hasattr(BaseTranslationClient, "provider_name")


class TestOllamaClient:
    """Testovi za OllamaClient."""

    def test_ollama_client_can_be_instantiated(self):
        """Test da se OllamaClient može kreirati."""
        from app.services.translation.clients.ollama import OllamaClient

        client = OllamaClient()

        assert client is not None

    def test_ollama_client_has_required_methods(self):
        """Test da OllamaClient ima sve potrebne metode."""
        from app.services.translation.clients.ollama import OllamaClient

        client = OllamaClient()

        assert hasattr(client, "translate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")
        assert callable(client.translate)
        assert callable(client.is_available)

    def test_ollama_provider_name(self):
        """Test provider_name property."""
        from app.services.translation.clients.ollama import OllamaClient

        client = OllamaClient()

        assert client.provider_name == "ollama"

    def test_ollama_is_available_with_mock(self):
        """Test is_available sa mock-ovanim httpx."""
        from app.services.translation.clients.ollama import OllamaClient

        with patch("httpx.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            client = OllamaClient()
            assert client.is_available() is True

    def test_ollama_is_available_when_not_available(self):
        """Test is_available kada Ollama nije dostupna."""
        from app.services.translation.clients.ollama import OllamaClient

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            client = OllamaClient()
            assert client.is_available() is False


class TestDeepLClient:
    """Testovi za DeepLClient."""

    def test_deepl_client_can_be_instantiated(self):
        """Test da se DeepLClient može kreirati."""
        from app.services.translation.clients.deepl import DeepLClient

        client = DeepLClient(api_key="test_key")

        assert client is not None

    def test_deepl_client_has_required_methods(self):
        """Test da DeepLClient ima sve potrebne metode."""
        from app.services.translation.clients.deepl import DeepLClient

        client = DeepLClient(api_key="test_key")

        assert hasattr(client, "translate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_deepl_provider_name(self):
        """Test provider_name property."""
        from app.services.translation.clients.deepl import DeepLClient

        client = DeepLClient(api_key="test_key")

        assert client.provider_name == "deepl"

    def test_deepl_is_available_with_key(self):
        """Test is_available kada ima API key."""
        from app.services.translation.clients.deepl import DeepLClient

        client = DeepLClient(api_key="test_key")

        assert client.is_available() is True

    def test_deepl_is_available_without_key(self):
        """Test is_available kada nema API key-ja."""
        from app.services.translation.clients.deepl import DeepLClient

        with patch("app.services.translation.clients.deepl.settings") as mock_settings:
            mock_settings.DEEPL_API_KEY = None

            client = DeepLClient()
            assert client.is_available() is False

    def test_deepl_language_mapping(self):
        """Test language mapping funkcije."""
        from app.services.translation.clients.deepl import DeepLClient

        client = DeepLClient(api_key="test_key")

        assert client._map_language("en") == "EN"
        assert client._map_language("sr") == "SR"
        assert client._map_language("de") == "DE"


class TestOpenAIClient:
    """Testovi za OpenAIClient."""

    def test_openai_client_can_be_instantiated(self):
        """Test da se OpenAIClient može kreirati."""
        from app.services.translation.clients.openai import OpenAIClient

        client = OpenAIClient(api_key="test_key")

        assert client is not None

    def test_openai_client_has_required_methods(self):
        """Test da OpenAIClient ima sve potrebne metode."""
        from app.services.translation.clients.openai import OpenAIClient

        client = OpenAIClient(api_key="test_key")

        assert hasattr(client, "translate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_openai_provider_name(self):
        """Test provider_name property."""
        from app.services.translation.clients.openai import OpenAIClient

        client = OpenAIClient(api_key="test_key")

        assert client.provider_name == "openai"

    def test_openai_cost_calculation(self):
        """Test izračunavanja cene."""
        from app.services.translation.clients.openai import OpenAIClient

        client = OpenAIClient(api_key="test_key", model="gpt-4")

        cost = client._calculate_cost(1000)
        assert cost == 0.03


class TestGoogleTranslateClient:
    """Testovi za GoogleTranslateClient."""

    def test_google_client_can_be_instantiated(self):
        """Test da se GoogleTranslateClient može kreirati."""
        from app.services.translation.clients.google import GoogleTranslateClient

        client = GoogleTranslateClient(api_key="test_key")

        assert client is not None

    def test_google_client_has_required_methods(self):
        """Test da GoogleTranslateClient ima sve potrebne metode."""
        from app.services.translation.clients.google import GoogleTranslateClient

        client = GoogleTranslateClient(api_key="test_key")

        assert hasattr(client, "translate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_google_provider_name(self):
        """Test provider_name property."""
        from app.services.translation.clients.google import GoogleTranslateClient

        client = GoogleTranslateClient(api_key="test_key")

        assert client.provider_name == "google"


class TestClaudeClient:
    """Testovi za ClaudeClient."""

    def test_claude_client_can_be_instantiated(self):
        """Test da se ClaudeClient može kreirati."""
        from app.services.translation.clients.claude import ClaudeClient

        client = ClaudeClient(api_key="test_key")

        assert client is not None

    def test_claude_client_has_required_methods(self):
        """Test da ClaudeClient ima sve potrebne metode."""
        from app.services.translation.clients.claude import ClaudeClient

        client = ClaudeClient(api_key="test_key")

        assert hasattr(client, "translate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_claude_provider_name(self):
        """Test provider_name property."""
        from app.services.translation.clients.claude import ClaudeClient

        client = ClaudeClient(api_key="test_key")

        assert client.provider_name == "claude"


class TestTranslationServiceIntegration:
    """Testovi za integraciju sa postojećim translation service-om."""

    def test_main_translation_file_imports(self):
        """Test da se glavni translation.py može importovati."""
        from app.services import translation

        assert translation is not None

    def test_translation_service_exists(self):
        """Test da translation_service postoji."""
        from app.services.translation import translation_service

        assert translation_service is not None

    def test_make_gemini_client_exists(self):
        """Test da make_gemini_client funkcija postoji."""
        from app.services.translation import make_gemini_client

        assert callable(make_gemini_client)

    def test_make_groq_client_exists(self):
        """Test da make_groq_client funkcija postoji."""
        from app.services.translation import make_groq_client

        assert callable(make_groq_client)

    def test_make_mistral_client_exists(self):
        """Test da make_mistral_client funkcija postoji."""
        from app.services.translation import make_mistral_client

        assert callable(make_mistral_client)


class TestTranslationModuleExports:
    """Testovi za module exports."""

    def test_clients_can_be_imported_from_main_module(self):
        """Test importovanja klijenata iz glavnog modula."""
        from app.services.translation import (
            OllamaClient,
            DeepLClient,
            OpenAIClient,
            GoogleTranslateClient,
            ClaudeClient,
        )

        assert OllamaClient is not None
        assert DeepLClient is not None
        assert OpenAIClient is not None
        assert GoogleTranslateClient is not None
        assert ClaudeClient is not None

    def test_translation_service_has_translate_method(self):
        """Test da translation_service ima translate metodu."""
        from app.services.translation import translation_service

        assert hasattr(translation_service, "translate")
        assert callable(translation_service.translate)


class TestBackwardCompatibility:
    """Testovi za backward compatibility."""

    def test_original_classes_still_work(self):
        """Test da originalne klase i dalje rade."""
        from app.services.translation import (
            TranslationProvider,
            TranslationResult,
            BaseTranslationClient,
            OllamaClient,
            DeepLClient,
            TranslationService,
        )

        # Sve klase treba da budu dostupne
        assert TranslationProvider is not None
        assert TranslationResult is not None
        assert BaseTranslationClient is not None
        assert OllamaClient is not None
        assert DeepLClient is not None
        assert TranslationService is not None

    def test_module_structure_intact(self):
        """Test da je struktura modula očuvana."""
        import app.services.translation as translation_module

        # Provera da ključni atributi postoje
        assert hasattr(translation_module, "translation_service")
        assert hasattr(translation_module, "TranslationProvider")
        assert hasattr(translation_module, "make_gemini_client")
        assert hasattr(translation_module, "make_groq_client")
        assert hasattr(translation_module, "make_mistral_client")
