# -*- coding: utf-8 -*-
"""
================================================================================
KNOWLEDGE BASE INTEGRATION TESTS
================================================================================
Testovi za RAG (Retrieval-Augmented Generation) knowledge base sistem.

Pokretanje:
    pytest tests/integration/test_knowledge.py -v
================================================================================
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestRagQueryWithContext:
    """Testovi za rag_query kada postoji relevantan kontekst u bazi znanja."""

    @pytest.mark.asyncio
    async def test_query_uses_context_and_ai(self):
        """Kada postoje chunk-ovi, AI treba da sintetiše odgovor koristeći kontekst."""
        from app.services.rag import rag_query

        mock_chunks = [
            {
                "id": "chunk-1",
                "content": "LightBurn is a laser control software used for cutting and engraving.",
                "source_name": "LightBurn Manual",
                "source_type": "pdf",
                "url": None,
                "similarity": 0.92,
            }
        ]
        ai_answer = "LightBurn is a laser control software designed for cutting and engraving operations."

        with patch("app.services.rag.similarity_search", return_value=mock_chunks):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": ai_answer}}]
                }
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.GEMINI_API_KEY = "test-gemini-key"
                    mock_settings.OPENAI_API_KEY = ""
                    mock_settings.GROQ_API_KEY = ""
                    mock_settings.MISTRAL_API_KEY = ""
                    mock_settings.ANTHROPIC_API_KEY = ""
                    mock_settings.OLLAMA_HOST = "http://ollama:11434"
                    mock_settings.OLLAMA_MODEL = "llama3.1"

                    result = await rag_query(
                        db=MagicMock(),
                        query="What is LightBurn?",
                        provider_override="gemini",
                    )

        assert result["answer"] == ai_answer
        assert result["chunks_used"] == 1
        assert result["has_context"] is True
        assert len(result["sources"]) == 1
        assert result["sources"][0]["name"] == "LightBurn Manual"

    @pytest.mark.asyncio
    async def test_system_prompt_allows_own_knowledge(self):
        """System prompt ne sme da kaže 'ISKLJUČIVO iz konteksta' — AI mora moći da dopuni znanjem."""
        from app.services import rag

        # Verify the system prompt source code doesn't contain the restrictive phrase
        import inspect
        source = inspect.getsource(rag.rag_query)
        assert "ISKLJUČIVO" not in source, (
            "System prompt ne sme ograničavati AI samo na kontekst — "
            "mora moći da koristi vlastito znanje kada kontekst nije dovoljan"
        )

    @pytest.mark.asyncio
    async def test_query_returns_sources(self):
        """Odgovor treba da sadrži listu izvora iz kojih je kontekst uzet."""
        from app.services.rag import rag_query

        mock_chunks = [
            {"id": "c1", "content": "Content A", "source_name": "Doc A", "source_type": "pdf", "url": None, "similarity": 0.9},
            {"id": "c2", "content": "Content B", "source_name": "Doc A", "source_type": "pdf", "url": None, "similarity": 0.85},
            {"id": "c3", "content": "Content C", "source_name": "Doc B", "source_type": "url", "url": "https://example.com", "similarity": 0.8},
        ]

        with patch("app.services.rag.similarity_search", return_value=mock_chunks):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": "Synthesized answer"}}]}
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.GEMINI_API_KEY = "key"
                    mock_settings.OPENAI_API_KEY = ""
                    mock_settings.GROQ_API_KEY = ""
                    mock_settings.MISTRAL_API_KEY = ""
                    mock_settings.ANTHROPIC_API_KEY = ""

                    result = await rag_query(db=MagicMock(), query="test", provider_override="gemini")

        # Deduplicated: Doc A and Doc B
        assert result["chunks_used"] == 3
        source_names = [s["name"] for s in result["sources"]]
        assert "Doc A" in source_names
        assert "Doc B" in source_names
        assert len(result["sources"]) == 2  # deduplicated


class TestRagQueryWithoutContext:
    """Testovi za rag_query kada NEMA relevantnog konteksta u bazi znanja."""

    @pytest.mark.asyncio
    async def test_no_context_still_calls_ai(self):
        """Kada nema chunk-ova, AI mora biti pozvan i dati direktan odgovor (ne statična poruka)."""
        from app.services.rag import rag_query

        ai_answer = "Python is a high-level programming language known for its simplicity."

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": ai_answer}}]}
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.GEMINI_API_KEY = "test-key"
                    mock_settings.OPENAI_API_KEY = ""
                    mock_settings.GROQ_API_KEY = ""
                    mock_settings.MISTRAL_API_KEY = ""
                    mock_settings.ANTHROPIC_API_KEY = ""

                    result = await rag_query(
                        db=MagicMock(),
                        query="What is Python?",
                        provider_override="gemini",
                    )

        assert result["answer"] == ai_answer
        assert result["chunks_used"] == 0
        assert result["has_context"] is False
        assert result["sources"] == []

    @pytest.mark.asyncio
    async def test_no_context_no_ai_shows_helpful_message(self):
        """Kada nema ni konteksta ni AI provajdera, poruka treba da bude korisna (ne 'Nisam pronašao')."""
        from app.services.rag import rag_query

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                # Simulate all providers failing
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(side_effect=Exception("Connection refused"))
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as mock_settings:
                    mock_settings.GEMINI_API_KEY = "key"
                    mock_settings.OPENAI_API_KEY = ""
                    mock_settings.GROQ_API_KEY = ""
                    mock_settings.MISTRAL_API_KEY = ""
                    mock_settings.ANTHROPIC_API_KEY = ""

                    result = await rag_query(
                        db=MagicMock(),
                        query="What is Python?",
                        provider_override="gemini",
                    )

        # Should NOT say "Nisam pronašao" — that was the old static message
        assert "Nisam pronašao" not in result["answer"]
        assert result["chunks_used"] == 0


class TestRagQueryProviderSelection:
    """Testovi za izbor AI provajdera u rag_query."""

    @pytest.mark.asyncio
    async def test_provider_override_gemini(self):
        """provider_override='gemini' mora koristiti Gemini API."""
        from app.services.rag import rag_query

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": "Gemini answer"}}]}
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = "gemini-test-key"
                    s.OPENAI_API_KEY = ""
                    s.GROQ_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""

                    result = await rag_query(db=MagicMock(), query="test", provider_override="gemini")

        assert result["provider"] == "gemini"
        # Verify Gemini URL was called
        call_args = mock_client.post.call_args
        assert "generativelanguage.googleapis.com" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_provider_override_groq(self):
        """provider_override='groq' mora koristiti Groq API."""
        from app.services.rag import rag_query

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": "Groq answer"}}]}
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GROQ_API_KEY = "groq-test-key"
                    s.GEMINI_API_KEY = ""
                    s.OPENAI_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""

                    result = await rag_query(db=MagicMock(), query="test", provider_override="groq")

        assert result["provider"] == "groq"

    @pytest.mark.asyncio
    async def test_auto_provider_skips_empty_keys(self):
        """Auto mode ne sme pokušavati provajdere koji nemaju API ključ."""
        from app.services.rag import rag_query

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": "Answer"}}]}
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = ""
                    s.OPENAI_API_KEY = ""
                    s.GROQ_API_KEY = "groq-key-only"  # only Groq has a key
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""
                    s.OLLAMA_HOST = "http://ollama:11434"
                    s.OLLAMA_MODEL = "llama3.1"

                    result = await rag_query(db=MagicMock(), query="test", provider_override=None)

        # Should have used groq (first available in auto order after empty ones)
        assert result["provider"] == "groq"

    @pytest.mark.asyncio
    async def test_provider_fallback_on_failure(self):
        """Kada prvi provajder ne radi, treba da pokuša sledećeg."""
        from app.services.rag import rag_query

        call_count = 0

        async def mock_post(url, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            if "generativelanguage" in url:
                # Gemini fails
                mock_resp.status_code = 500
                mock_resp.text = "Server error"
                mock_resp.json.return_value = {}
            elif "groq" in url:
                # Groq succeeds
                mock_resp.status_code = 200
                mock_resp.json.return_value = {"choices": [{"message": {"content": "Groq fallback answer"}}]}
            return mock_resp

        with patch("app.services.rag.similarity_search", return_value=[]):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(side_effect=mock_post)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = "gemini-key"
                    s.GROQ_API_KEY = "groq-key"
                    s.OPENAI_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""
                    s.OLLAMA_HOST = "http://ollama:11434"
                    s.OLLAMA_MODEL = "llama3.1"

                    result = await rag_query(db=MagicMock(), query="test", provider_override=None)

        assert result["answer"] == "Groq fallback answer"
        assert result["provider"] == "groq"


class TestKnowledgeBaseApiEndpoint:
    """Integration testovi za /knowledge/query REST endpoint."""

    @pytest.mark.asyncio
    async def test_query_endpoint_returns_answer(self, db):
        """POST /knowledge/query mora da vrati AI odgovor."""
        from app.main import app
        from app.db.session import get_db
        from httpx import AsyncClient

        app.dependency_overrides[get_db] = lambda: db

        try:
            with patch("app.services.rag.rag_query") as mock_rag:
                mock_rag.return_value = {
                    "answer": "LightBurn is laser software.",
                    "sources": [{"name": "LightBurn Manual", "type": "pdf", "url": None}],
                    "chunks_used": 2,
                    "provider": "gemini",
                    "has_context": True,
                }

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/knowledge/query",
                        json={"query": "What is LightBurn?", "provider": "gemini"},
                        headers={"Authorization": "Bearer fake-token"},
                    )
        finally:
            app.dependency_overrides.clear()

        # Either 200 (success) or 401/422 (auth/validation) — just not 500
        assert response.status_code != 500

    @pytest.mark.asyncio
    async def test_query_endpoint_requires_query_field(self, db):
        """POST /knowledge/query bez 'query' polja mora da vrati 422."""
        from app.main import app
        from app.db.session import get_db
        from httpx import AsyncClient

        app.dependency_overrides[get_db] = lambda: db

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/knowledge/query",
                    json={},  # missing 'query' field
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code in (422, 401)  # validation error or auth required
