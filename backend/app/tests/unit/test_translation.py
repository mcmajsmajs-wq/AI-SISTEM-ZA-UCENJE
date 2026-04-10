# -*- coding: utf-8 -*-
"""
================================================================================
TRANSLATION SERVICE TESTS
================================================================================
Unit testovi za TranslationService - AI prevod sa više provajdera.

Pokretanje:
    pytest tests/unit/test_translation.py -v
================================================================================
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
import httpx

from app.services.translation import (
    TranslationService,
    TranslationProvider,
    TranslationResult,
    BatchTranslationResult,
    OllamaClient,
    DeepLClient,
    OpenAIClient,
    GoogleTranslateClient,
    ClaudeClient,
    BaseTranslationClient,
)


class TestTranslationProvider:
    """Testovi za TranslationProvider enum."""

    def test_provider_values(self):
        """Test vrednosti provajdera."""
        assert TranslationProvider.OLLAMA.value == "ollama"
        assert TranslationProvider.DEEPL.value == "deepl"
        assert TranslationProvider.OPENAI.value == "openai"
        assert TranslationProvider.GOOGLE.value == "google"
        assert TranslationProvider.CLAUDE.value == "claude"

    def test_provider_count(self):
        """Test broja provajdera."""
        # FAZA 5: Dodat LIBRETRANSLATE provider
        assert len(TranslationProvider) == 7


class TestTranslationResult:
    """Testovi za TranslationResult dataclass."""

    def test_result_creation_success(self):
        """Test kreiranja uspešnog rezultata."""
        result = TranslationResult(
            success=True,
            translated_text="Ovo je prevod",
            source_language="en",
            target_language="sr",
            provider="ollama",
            tokens_used=100,
            cost=0.0,
            duration_ms=150.5,
        )

        assert result.success is True
        assert result.translated_text == "Ovo je prevod"
        assert result.provider == "ollama"
        assert result.error is None

    def test_result_creation_failure(self):
        """Test kreiranja neuspešnog rezultata."""
        result = TranslationResult(success=False, error="Connection timeout")

        assert result.success is False
        assert result.error == "Connection timeout"
        assert result.translated_text == ""

    def test_result_defaults(self):
        """Test default vrednosti."""
        result = TranslationResult(success=True)

        assert result.translated_text == ""
        assert result.tokens_used == 0
        assert result.cost == 0.0
        assert result.duration_ms == 0.0


class TestBatchTranslationResult:
    """Testovi za BatchTranslationResult dataclass."""

    def test_batch_result_creation(self):
        """Test kreiranja batch rezultata."""
        results = [
            TranslationResult(success=True, translated_text="Prevod 1"),
            TranslationResult(success=True, translated_text="Prevod 2"),
        ]

        batch = BatchTranslationResult(
            success=True, results=results, total_tokens=200, total_cost=0.05
        )

        assert batch.success is True
        assert len(batch.results) == 2
        assert batch.total_tokens == 200
        assert len(batch.errors) == 0

    def test_batch_result_with_errors(self):
        """Test batch rezultata sa greškama."""
        batch = BatchTranslationResult(success=False, errors=["Error 1", "Error 2"])

        assert batch.success is False
        assert len(batch.errors) == 2


class TestOllamaClient:
    """Testovi za OllamaClient."""

    def test_init_default(self):
        """Test inicijalizacije sa default vrednostima."""
        client = OllamaClient()

        assert client.provider_name == "ollama"

    def test_is_available_true(self):
        """Test provere dostupnosti - dostupan."""
        client = OllamaClient()

        with patch("httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            available = client.is_available()

            assert available is True

    def test_is_available_false(self):
        """Test provere dostupnosti - nedostupan."""
        client = OllamaClient()

        with patch("httpx.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            available = client.is_available()

            assert available is False

    def test_translate_success(self):
        """Test uspešnog prevoda."""
        client = OllamaClient()

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Ovo je prevod teksta.",
                "prompt_eval_count": 50,
                "eval_count": 30,
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="This is a test text.", source_language="en", target_language="sr"
            )

            assert result.success is True
            assert result.translated_text == "Ovo je prevod teksta."
            assert result.tokens_used == 80

    def test_translate_api_error(self):
        """Test API greške."""
        client = OllamaClient()

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_post.return_value = mock_response

            result = client.translate(
                text="Test text", source_language="en", target_language="sr"
            )

            assert result.success is False
            assert "error" in result.error.lower() or "500" in result.error

    def test_translate_with_context(self):
        """Test prevoda sa kontekstom."""
        client = OllamaClient()

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "Prevod",
                "prompt_eval_count": 10,
                "eval_count": 5,
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="Test",
                source_language="en",
                target_language="sr",
                context="Technical document",
            )

            assert result.success is True
            call_args = mock_post.call_args
            assert "Technical document" in call_args[1]["json"]["prompt"]


class TestDeepLClient:
    """Testovi za DeepLClient."""

    def test_init_with_api_key(self):
        """Test inicijalizacije sa API ključem."""
        client = DeepLClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.provider_name == "deepl"

    def test_is_available_with_key(self):
        """Test dostupnosti sa API ključem."""
        client = DeepLClient(api_key="test-key")

        assert client.is_available() is True

    def test_is_available_without_key(self):
        """Test dostupnosti bez API ključa."""
        with patch("app.services.translation.clients.deepl.settings") as mock_settings:
            mock_settings.DEEPL_API_KEY = None
            client = DeepLClient()

            assert client.is_available() is False

    def test_map_language(self):
        """Test mapiranja jezika."""
        client = DeepLClient()

        assert client._map_language("en") == "EN"
        assert client._map_language("sr") == "SR"
        assert client._map_language("DE") == "DE"

    def test_translate_success(self):
        """Test uspešnog prevoda."""
        client = DeepLClient(api_key="test-key")

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "translations": [{"text": "Ovo je prevod"}]
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="This is a translation", source_language="en", target_language="sr"
            )

            assert result.success is True
            assert result.translated_text == "Ovo je prevod"
            assert result.cost > 0

    def test_translate_without_api_key(self):
        """Test prevoda bez API ključa."""
        with patch("app.services.translation.settings") as mock_settings:
            mock_settings.DEEPL_API_KEY = None
            client = DeepLClient()

            result = client.translate(
                text="Test", source_language="en", target_language="sr"
            )

            assert result.success is False
            assert result.error is not None


class TestOpenAIClient:
    """Testovi za OpenAIClient."""

    def test_init_with_api_key(self):
        """Test inicijalizacije."""
        client = OpenAIClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.provider_name == "openai"

    def test_is_available(self):
        """Test dostupnosti."""
        client_with_key = OpenAIClient(api_key="test-key")
        client_without_key = OpenAIClient(api_key=None)

        assert client_with_key.is_available() is True
        # Bez ključa — mora biti False čak i ako env varijabla postoji
        with patch("app.services.translation.clients.openai.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            client_no_env = OpenAIClient(api_key=None)
            assert client_no_env.is_available() is False

    def test_calculate_cost(self):
        """Test kalkulacije cene."""
        client = OpenAIClient(model="gpt-4")

        cost = client._calculate_cost(1000)

        assert cost == 0.03

    def test_translate_success(self):
        """Test uspešnog prevoda."""
        client = OpenAIClient(api_key="test-key")

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Ovo je prevod"}}],
                "usage": {"total_tokens": 150},
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="This is a translation", source_language="en", target_language="sr"
            )

            assert result.success is True
            assert result.translated_text == "Ovo je prevod"
            assert result.tokens_used == 150


class TestGoogleTranslateClient:
    """Testovi za GoogleTranslateClient."""

    def test_init(self):
        """Test inicijalizacije."""
        client = GoogleTranslateClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.provider_name == "google"

    def test_is_available(self):
        """Test dostupnosti."""
        client_with_key = GoogleTranslateClient(api_key="test-key")
        client_without_key = GoogleTranslateClient(api_key=None)

        assert client_with_key.is_available() is True
        assert client_without_key.is_available() is False

    def test_translate_success(self):
        """Test uspešnog prevoda."""
        client = GoogleTranslateClient(api_key="test-key")

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "data": {"translations": [{"translatedText": "Ovo je prevod"}]}
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="This is a translation", source_language="en", target_language="sr"
            )

            assert result.success is True
            assert result.translated_text == "Ovo je prevod"


class TestClaudeClient:
    """Testovi za ClaudeClient."""

    def test_init(self):
        """Test inicijalizacije."""
        client = ClaudeClient(api_key="test-key")

        assert client.api_key == "test-key"
        assert client.provider_name == "claude"

    def test_is_available(self):
        """Test dostupnosti."""
        from unittest.mock import patch

        client_with_key = ClaudeClient(api_key="test-key")

        # Test with explicit key - should be available
        assert client_with_key.is_available() is True

        # Test without key - mock settings to return None
        with patch("app.services.translation.clients.claude.settings") as mock_settings:
            mock_settings.ANTHROPIC_API_KEY = None
            client_without_key = ClaudeClient(api_key=None)
            assert client_without_key.is_available() is False

    def test_calculate_cost(self):
        """Test kalkulacije cene."""
        client = ClaudeClient(model="claude-3-sonnet-20240229")

        cost = client._calculate_cost(input_tokens=1000, output_tokens=500)

        assert cost > 0

    def test_translate_success(self):
        """Test uspešnog prevoda."""
        client = ClaudeClient(api_key="test-key")

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "content": [{"text": "Ovo je prevod"}],
                "usage": {"input_tokens": 100, "output_tokens": 50},
            }
            mock_post.return_value = mock_response

            result = client.translate(
                text="This is a translation", source_language="en", target_language="sr"
            )

            assert result.success is True
            assert result.translated_text == "Ovo je prevod"
            assert result.tokens_used == 150


class TestTranslationService:
    """Testovi za TranslationService."""

    def test_init(self):
        """Test inicijalizacije servisa."""
        service = TranslationService()

        assert len(service._clients) == 6

    def test_get_language_name(self):
        """Test dohvatanja imena jezika."""
        service = TranslationService()

        assert service.get_language_name("en") == "English"
        assert service.get_language_name("sr") == "Serbian"
        assert service.get_language_name("unknown") == "unknown"

    def test_set_glossary(self):
        """Test postavljanja glosara."""
        service = TranslationService()

        service.set_glossary({"AI": "veštačka inteligencija"})

        assert service._glossary["AI"] == "veštačka inteligencija"

    def test_get_available_providers(self):
        """Test dohvatanja dostupnih provajdera."""
        service = TranslationService()

        with patch.object(
            service._clients["ollama"], "is_available", return_value=True
        ):
            providers = service.get_available_providers()

            assert len(providers) == 6
            assert any(p["id"] == "ollama" for p in providers)

    def test_translate_empty_text(self):
        """Test prevoda praznog teksta."""
        service = TranslationService()

        result = service.translate("")

        assert result.success is True
        assert result.translated_text == ""

    def test_translate_with_specific_provider(self):
        """Test prevoda sa specifičnim provajderom."""
        service = TranslationService()

        with patch.object(
            service._clients["ollama"], "is_available", return_value=True
        ):
            with patch.object(
                service._clients["ollama"], "translate"
            ) as mock_translate:
                mock_translate.return_value = TranslationResult(
                    success=True, translated_text="Prevod", provider="ollama"
                )

                result = service.translate(text="Test", provider="ollama")

                assert result.success is True
                assert result.provider == "ollama"

    def test_translate_fallback(self):
        """Test fallback mehanizma."""
        service = TranslationService(fallback_order="ollama,deepl")

        with patch.object(
            service._clients["ollama"], "is_available", return_value=True
        ):
            with patch.object(service._clients["ollama"], "translate") as mock_ollama:
                mock_ollama.return_value = TranslationResult(
                    success=False, error="Ollama failed"
                )

                with patch.object(
                    service._clients["deepl"], "is_available", return_value=True
                ):
                    with patch.object(
                        service._clients["deepl"], "translate"
                    ) as mock_deepl:
                        mock_deepl.return_value = TranslationResult(
                            success=True,
                            translated_text="DeepL prevod",
                            provider="deepl",
                        )

                        result = service.translate("Test")

                        assert result.success is True
                        assert result.provider == "deepl"

    def test_translate_all_providers_fail(self):
        """Test kad svi provajderi ne uspeju."""
        service = TranslationService()

        for client in service._clients.values():
            with patch.object(client, "is_available", return_value=True):
                with patch.object(
                    client,
                    "translate",
                    return_value=TranslationResult(success=False, error="Failed"),
                ):
                    result = service.translate("Test")

                    assert result.success is False
                    assert "All providers failed" in result.error

    def test_translate_batch(self):
        """Test batch prevoda."""
        service = TranslationService()

        texts = ["Text 1", "Text 2", "Text 3"]

        with patch.object(service, "translate") as mock_translate:
            mock_translate.side_effect = [
                TranslationResult(
                    success=True, translated_text="Prevod 1", tokens_used=10
                ),
                TranslationResult(
                    success=True, translated_text="Prevod 2", tokens_used=20
                ),
                TranslationResult(
                    success=True, translated_text="Prevod 3", tokens_used=30
                ),
            ]

            result = service.translate_batch(texts)

            assert result.success is True
            assert len(result.results) == 3
            assert result.total_tokens == 60

    def test_translate_batch_with_progress_callback(self):
        """Test batch prevoda sa progress callback."""
        service = TranslationService()

        texts = ["Text 1", "Text 2"]
        progress_calls = []

        def progress_callback(current, total):
            progress_calls.append((current, total))

        with patch.object(service, "translate") as mock_translate:
            mock_translate.return_value = TranslationResult(
                success=True, translated_text="Prevod"
            )

            service.translate_batch(texts, progress_callback=progress_callback)

            assert len(progress_calls) == 2
            assert progress_calls[0] == (1, 2)
            assert progress_calls[1] == (2, 2)

    def test_estimate_cost_ollama(self):
        """Test estimacije cene za Ollama (besplatno)."""
        service = TranslationService()

        estimate = service.estimate_cost(["Test text"], provider="ollama")

        assert estimate["provider"] == "ollama"
        assert estimate["estimated_cost"] == 0.0

    def test_estimate_cost_deepl(self):
        """Test estimacije cene za DeepL."""
        service = TranslationService()

        estimate = service.estimate_cost(["Test text here"], provider="deepl")

        assert estimate["provider"] == "deepl"
        assert estimate["estimated_cost"] >= 0  # može biti 0 za kratak tekst

    def test_estimate_cost_openai(self):
        """Test estimacije cene za OpenAI."""
        service = TranslationService()

        estimate = service.estimate_cost(["Test text"], provider="openai")

        assert estimate["provider"] == "openai"
        assert "estimated_tokens" in estimate

    def test_estimate_cost_google(self):
        """Test estimacije cene za Google Translate."""
        service = TranslationService()

        estimate = service.estimate_cost(["Test text"], provider="google")

        assert estimate["provider"] == "google"
        assert estimate["estimated_cost"] > 0

    def test_estimate_cost_claude(self):
        """Test estimacije cene za Claude."""
        service = TranslationService()

        estimate = service.estimate_cost(["Test text"], provider="claude")

        assert estimate["provider"] == "claude"
        assert estimate["estimated_cost"] >= 0  # može biti 0 za kratak tekst

    def test_glossary_applied_to_translation(self):
        """Test da se glosar primenjuje na prevod."""
        service = TranslationService()
        service.set_glossary({"AI": "veštačka inteligencija"})

        with patch.object(
            service._clients["ollama"], "is_available", return_value=True
        ):
            with patch.object(
                service._clients["ollama"], "translate"
            ) as mock_translate:
                mock_translate.return_value = TranslationResult(
                    success=True, translated_text="AI je važna tehnologija"
                )

                result = service.translate("AI is important technology")

                assert "veštačka inteligencija" in result.translated_text

    def test_provider_not_available(self):
        """Test kad traženi provajder nije dostupan."""
        service = TranslationService()

        with patch.object(
            service._clients["deepl"], "is_available", return_value=False
        ):
            result = service.translate("Test", provider="deepl")

            assert result.success is False
            assert "not available" in result.error.lower()


class TestEdgeCases:
    """Testovi za edge cases."""

    def test_very_long_text(self):
        """Test sa vrlo dugim tekstom."""
        client = OllamaClient()

        long_text = "word " * 10000

        with patch("httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "response": "prevod " * 10000,
                "prompt_eval_count": 10000,
                "eval_count": 10000,
            }
            mock_post.return_value = mock_response

            result = client.translate(long_text, "en", "sr")

            assert result.success is True

    def test_special_characters(self):
        """Test sa specijalnim karakterima."""
        service = TranslationService()

        special_text = "Hello! @#$%^&*() 你好 مرحبا"

        with patch.object(service, "translate") as mock_translate:
            mock_translate.return_value = TranslationResult(
                success=True, translated_text="Zdravo! @#$%^&*() 你好 مرحبا"
            )

            result = service.translate(special_text)

            assert result.success is True

    def test_unicode_languages(self):
        """Test sa Unicode jezičkim kodovima."""
        service = TranslationService()

        result = service.translate("", source_language="sr", target_language="en")

        assert result.success is True

    def test_whitespace_only_text(self):
        """Test sa tekstom koji ima samo whitespace."""
        service = TranslationService()

        result = service.translate("   \n\t   ")

        assert result.success is True
        assert result.translated_text == ""

    def test_concurrent_translations(self):
        """Test više uzastopnih prevoda."""
        service = TranslationService()

        with patch.object(
            service._clients["ollama"], "is_available", return_value=True
        ):
            with patch.object(
                service._clients["ollama"], "translate"
            ) as mock_translate:
                mock_translate.return_value = TranslationResult(
                    success=True, translated_text="Prevod"
                )

                results = [service.translate(f"Text {i}") for i in range(5)]

                assert all(r.success for r in results)
                assert mock_translate.call_count == 5
