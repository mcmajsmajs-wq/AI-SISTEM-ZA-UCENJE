# -*- coding: utf-8 -*-
"""
================================================================================
TEST QUIZ CLIENTS - Phase 1: AI Providers Extraction
================================================================================

Testovi za verifikaciju Phase 1 implementacije:
- BaseQuizClient apstraktna klasa
- OllamaQuizClient
- OpenAIQuizClient
- ClaudeQuizClient
- OpenAICompatQuizClient (gemini, groq, mistral, deepseek)
- Factory funkcije (_build_clients, get_clients, get_available_providers)

Verzija: 1.0.0
================================================================================
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict


class TestBaseQuizClient:
    """Testovi za BaseQuizClient apstraktnu klasu."""

    def test_base_class_is_abstract(self):
        """Test da je BaseQuizClient zaista apstraktna klasa."""
        from app.services.quiz.clients.base import BaseQuizClient

        # Pokušaj kreiranja instance treba da baci grešku
        with pytest.raises(TypeError):
            BaseQuizClient()

    def test_base_class_has_abstract_methods(self):
        """Test da BaseQuizClient ima sve potrebne apstraktne metode."""
        from app.services.quiz.clients.base import BaseQuizClient

        # Proveri da postoje apstraktne metode
        assert hasattr(BaseQuizClient, "generate")
        assert hasattr(BaseQuizClient, "is_available")
        assert hasattr(BaseQuizClient, "provider_name")

    def test_base_class_has_abstract_property(self):
        """Test da provider_name property postoji."""
        from app.services.quiz.clients.base import BaseQuizClient

        # Proveri da je property definisan
        assert hasattr(BaseQuizClient, "provider_name")


class TestOllamaQuizClient:
    """Testovi za OllamaQuizClient."""

    def test_ollama_client_can_be_instantiated(self):
        """Test da se OllamaQuizClient može instancirati."""
        from app.services.quiz.clients.ollama import OllamaQuizClient

        client = OllamaQuizClient()
        assert client is not None

    def test_ollama_client_has_required_methods(self):
        """Test da OllamaQuizClient ima sve potrebne metode."""
        from app.services.quiz.clients.ollama import OllamaQuizClient

        client = OllamaQuizClient()
        assert hasattr(client, "generate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_ollama_client_provider_name(self):
        """Test da provider_name vraća 'ollama'."""
        from app.services.quiz.clients.ollama import OllamaQuizClient

        client = OllamaQuizClient()
        assert client.provider_name == "ollama"

    @patch("httpx.Client")
    def test_ollama_generate_returns_tuple(self, mock_client_class):
        """Test da generate vraća tuple (bool, str, str)."""
        from app.services.quiz.clients.ollama import OllamaQuizClient

        # Mock the response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": '[{"question_text": "Test?", "question_type": "multiple_choice", "options": ["A", "B"], "correct_answer": "A"}]'
        }

        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OllamaQuizClient()
        result = client.generate("Test text", 5)

        assert isinstance(result, tuple)
        assert len(result) == 3
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
        assert isinstance(result[2], str)

    @patch("httpx.Client")
    def test_ollama_is_available_returns_bool(self, mock_client_class):
        """Test da is_available vraća bool."""
        from app.services.quiz.clients.ollama import OllamaQuizClient

        mock_response = Mock()
        mock_response.status_code = 200

        mock_client = Mock()
        mock_client.__enter__ = Mock(return_value=mock_client)
        mock_client.__exit__ = Mock(return_value=False)
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        client = OllamaQuizClient()
        result = client.is_available()

        assert isinstance(result, bool)


class TestOpenAIQuizClient:
    """Testovi za OpenAIQuizClient."""

    def test_openai_client_can_be_instantiated(self):
        """Test da se OpenAIQuizClient može instancirati."""
        from app.services.quiz.clients.openai import OpenAIQuizClient

        client = OpenAIQuizClient()
        assert client is not None

    def test_openai_client_has_required_methods(self):
        """Test da OpenAIQuizClient ima sve potrebne metode."""
        from app.services.quiz.clients.openai import OpenAIQuizClient

        client = OpenAIQuizClient()
        assert hasattr(client, "generate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_openai_client_provider_name(self):
        """Test da provider_name vraća 'openai'."""
        from app.services.quiz.clients.openai import OpenAIQuizClient

        client = OpenAIQuizClient()
        assert client.provider_name == "openai"

    def test_openai_client_has_api_key_attribute(self):
        """Test da OpenAIQuizClient ima api_key atribut."""
        from app.services.quiz.clients.openai import OpenAIQuizClient

        client = OpenAIQuizClient()
        assert hasattr(client, "api_key")


class TestClaudeQuizClient:
    """Testovi za ClaudeQuizClient."""

    def test_claude_client_can_be_instantiated(self):
        """Test da se ClaudeQuizClient može instancirati."""
        from app.services.quiz.clients.claude import ClaudeQuizClient

        client = ClaudeQuizClient()
        assert client is not None

    def test_claude_client_has_required_methods(self):
        """Test da ClaudeQuizClient ima sve potrebne metode."""
        from app.services.quiz.clients.claude import ClaudeQuizClient

        client = ClaudeQuizClient()
        assert hasattr(client, "generate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    def test_claude_client_provider_name(self):
        """Test da provider_name vraća 'claude'."""
        from app.services.quiz.clients.claude import ClaudeQuizClient

        client = ClaudeQuizClient()
        assert client.provider_name == "claude"

    def test_claude_client_has_api_key_attribute(self):
        """Test da ClaudeQuizClient ima api_key atribut."""
        from app.services.quiz.clients.claude import ClaudeQuizClient

        client = ClaudeQuizClient()
        assert hasattr(client, "api_key")


class TestOpenAICompatQuizClient:
    """Testovi za OpenAICompatQuizClient (gemini, groq, mistral, deepseek)."""

    @pytest.mark.parametrize("provider_name", ["gemini", "groq", "mistral", "deepseek"])
    def test_compat_client_can_be_instantiated(self, provider_name):
        """Test da se OpenAICompatQuizClient može instancirati za svaki provider."""
        from app.services.quiz.clients.openai_compat import OpenAICompatQuizClient

        client = OpenAICompatQuizClient(
            provider_name,
            f"https://api.{provider_name}.com/v1",
            f"test-model",
            "test-key",
        )
        assert client is not None

    @pytest.mark.parametrize("provider_name", ["gemini", "groq", "mistral", "deepseek"])
    def test_compat_client_has_required_methods(self, provider_name):
        """Test da OpenAICompatQuizClient ima potrebne metode."""
        from app.services.quiz.clients.openai_compat import OpenAICompatQuizClient

        client = OpenAICompatQuizClient(
            provider_name,
            f"https://api.{provider_name}.com/v1",
            f"test-model",
            "test-key",
        )
        assert hasattr(client, "generate")
        assert hasattr(client, "is_available")
        assert hasattr(client, "provider_name")

    @pytest.mark.parametrize("provider_name", ["gemini", "groq", "mistral", "deepseek"])
    def test_compat_client_provider_name(self, provider_name):
        """Test da provider_name vraća ispravan naziv."""
        from app.services.quiz.clients.openai_compat import OpenAICompatQuizClient

        client = OpenAICompatQuizClient(
            provider_name,
            f"https://api.{provider_name}.com/v1",
            f"test-model",
            "test-key",
        )
        assert client.provider_name == provider_name


class TestClientsFactory:
    """Testovi za factory funkcije."""

    def test_build_clients_returns_dict(self):
        """Test da _build_clients vraća dictionary."""
        from app.services.quiz.clients import _build_clients

        clients = _build_clients()
        assert isinstance(clients, dict)

    def test_build_clients_has_all_providers(self):
        """Test da _build_clients sadrži sve providere."""
        from app.services.quiz.clients import _build_clients

        clients = _build_clients()
        expected = [
            "ollama",
            "openai",
            "claude",
            "gemini",
            "groq",
            "mistral",
            "deepseek",
        ]

        for provider in expected:
            assert provider in clients, f"Provider {provider} not found in clients"

    def test_build_clients_with_user_keys(self):
        """Test da _build_clients prihvata korisničke ključeve."""
        from app.services.quiz.clients import _build_clients

        clients = _build_clients(
            user_openai_key="test-openai-key", user_claude_key="test-claude-key"
        )

        assert clients["openai"].api_key == "test-openai-key"
        assert clients["claude"].api_key == "test-claude-key"

    def test_get_clients_returns_dict(self):
        """Test da get_clients vraća dictionary."""
        from app.services.quiz.clients import get_clients

        clients = get_clients()
        assert isinstance(clients, dict)

    def test_get_clients_has_all_providers(self):
        """Test da get_clients sadrži sve providere."""
        from app.services.quiz.clients import get_clients

        clients = get_clients()
        expected = [
            "ollama",
            "openai",
            "claude",
            "gemini",
            "groq",
            "mistral",
            "deepseek",
        ]

        for provider in expected:
            assert provider in clients

    def test_get_provider_returns_client(self):
        """Test da get_provider vraća specifičnog klijenta."""
        from app.services.quiz.clients import get_provider

        client = get_provider("ollama")
        assert client is not None
        assert client.provider_name == "ollama"

    def test_get_provider_unknown_returns_none(self):
        """Test da get_provider za nepoznati provider vraća None."""
        from app.services.quiz.clients import get_provider

        client = get_provider("unknown_provider")
        assert client is None

    def test_get_available_providers_returns_list(self):
        """Test da get_available_providers vraća listu."""
        from app.services.quiz.clients import get_available_providers

        providers = get_available_providers()
        assert isinstance(providers, list)

    def test_get_available_providers_has_all_providers(self):
        """Test da get_available_providers vraća sve providere."""
        from app.services.quiz.clients import get_available_providers

        providers = get_available_providers()
        provider_ids = [p["id"] for p in providers]

        expected = [
            "ollama",
            "openai",
            "claude",
            "gemini",
            "groq",
            "mistral",
            "deepseek",
        ]
        for provider in expected:
            assert provider in provider_ids, f"Provider {provider} not in list"

    def test_get_available_providers_has_type_field(self):
        """Test da svaki provider ima 'type' polje."""
        from app.services.quiz.clients import get_available_providers

        providers = get_available_providers()

        for provider in providers:
            assert "type" in provider
            assert provider["type"] in ["local", "online"]

    def test_get_available_providers_has_available_field(self):
        """Test da svaki provider ima 'available' polje."""
        from app.services.quiz.clients import get_available_providers

        providers = get_available_providers()

        for provider in providers:
            assert "available" in provider
            assert isinstance(provider["available"], bool)


class TestProviderOrder:
    """Testovi za _PROVIDER_ORDER konstantu."""

    def test_provider_order_exists(self):
        """Test da _PROVIDER_ORDER postoji."""
        from app.services.quiz.clients import _PROVIDER_ORDER

        assert _PROVIDER_ORDER is not None
        assert isinstance(_PROVIDER_ORDER, list)

    def test_provider_order_has_correct_providers(self):
        """Test da _PROVIDER_ORDER sadrži sve providere."""
        from app.services.quiz.clients import _PROVIDER_ORDER

        expected = [
            "groq",
            "openai",
            "claude",
            "gemini",
            "mistral",
            "deepseek",
            "ollama",
        ]
        assert set(_PROVIDER_ORDER) == set(expected)

    def test_provider_order_first_is_groq(self):
        """Test da je Groq prvi u listi (najviši prioritet)."""
        from app.services.quiz.clients import _PROVIDER_ORDER

        assert _PROVIDER_ORDER[0] == "groq"

    def test_provider_order_last_is_ollama(self):
        """Test da je Ollama poslednji u listi (najniži prioritet)."""
        from app.services.quiz.clients import _PROVIDER_ORDER

        assert _PROVIDER_ORDER[-1] == "ollama"


class TestClientIntegration:
    """Integration testovi za klijente."""

    def test_all_clients_inherit_from_base(self):
        """Test da svi klijenti nasleđuju BaseQuizClient."""
        from app.services.quiz.clients import get_clients
        from app.services.quiz.clients.base import BaseQuizClient

        clients = get_clients()

        for name, client in clients.items():
            assert isinstance(client, BaseQuizClient), (
                f"{name} does not inherit from BaseQuizClient"
            )

    def test_all_clients_implement_generate(self):
        """Test da svi klijenti implementiraju generate metodu."""
        from app.services.quiz.clients import get_clients

        clients = get_clients()

        for name, client in clients.items():
            assert callable(client.generate), f"{name}.generate is not callable"

    def test_all_clients_implement_is_available(self):
        """Test da svi klijenti implementiraju is_available metodu."""
        from app.services.quiz.clients import get_clients

        clients = get_clients()

        for name, client in clients.items():
            assert callable(client.is_available), f"{name}.is_available is not callable"

    def test_all_clients_have_provider_name(self):
        """Test da svi klijenti imaju provider_name property."""
        from app.services.quiz.clients import get_clients

        clients = get_clients()

        for name, client in clients.items():
            assert hasattr(client, "provider_name"), f"{name} has no provider_name"
            assert isinstance(client.provider_name, str), (
                f"{name}.provider_name is not str"
            )


class TestBackwardCompatibility:
    """Testovi za backward compatibility."""

    def test_clients_module_exports(self):
        """Test da clients modul ima sve potrebne eksporte."""
        from app.services import quiz

        # Proveri da li moduli postoje
        assert hasattr(quiz.clients, "BaseQuizClient")
        assert hasattr(quiz.clients, "OllamaQuizClient")
        assert hasattr(quiz.clients, "OpenAIQuizClient")
        assert hasattr(quiz.clients, "ClaudeQuizClient")
        assert hasattr(quiz.clients, "OpenAICompatQuizClient")
        assert hasattr(quiz.clients, "_build_clients")
        assert hasattr(quiz.clients, "get_clients")
        assert hasattr(quiz.clients, "get_provider")
        assert hasattr(quiz.clients, "get_available_providers")

    def test_imports_work_from_service_package(self):
        """Test da se može importovati preko app.services.quiz.clients."""
        from app.services.quiz.clients import (
            BaseQuizClient,
            OllamaQuizClient,
            OpenAIQuizClient,
            ClaudeQuizClient,
            OpenAICompatQuizClient,
            _build_clients,
            get_clients,
            get_provider,
            get_available_providers,
        )

        assert BaseQuizClient is not None
        assert OllamaQuizClient is not None
        assert OpenAIQuizClient is not None
        assert ClaudeQuizClient is not None
        assert OpenAICompatQuizClient is not None
        assert _build_clients is not None
        assert get_clients is not None
        assert get_provider is not None
        assert get_available_providers is not None
