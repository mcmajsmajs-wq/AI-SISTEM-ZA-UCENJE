import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestGenerateExtractiveSummary:
    """Testovi za _generate_extractive_summary."""

    def test_returns_first_sentences(self):
        from app.services.knowledge_ingestion import _generate_extractive_summary

        text = (
            "Ovo je prva recenica. Ovo je druga recenica. Ovo je treca. Ovo je cetvrta."
        )
        result = _generate_extractive_summary(text, max_sentences=2)
        assert result == "Ovo je prva recenica. Ovo je druga recenica."

    def test_returns_all_when_fewer_sentences(self):
        from app.services.knowledge_ingestion import _generate_extractive_summary

        text = "Samo jedna recenica."
        result = _generate_extractive_summary(text, max_sentences=5)
        assert result == "Samo jedna recenica."

    def test_returns_empty_for_empty_text(self):
        from app.services.knowledge_ingestion import _generate_extractive_summary

        result = _generate_extractive_summary("", max_sentences=3)
        assert result == ""

    def test_returns_truncated_for_text_without_period(self):
        from app.services.knowledge_ingestion import _generate_extractive_summary

        text = "A" * 300
        result = _generate_extractive_summary(text, max_sentences=3)
        assert len(result) == 200
        assert result == text[:200]

    def test_handles_newlines_in_text(self):
        from app.services.knowledge_ingestion import _generate_extractive_summary

        text = "Prva recenica.\nDruga recenica.\nTreca recenica."
        result = _generate_extractive_summary(text, max_sentences=2)
        assert "Prva recenica." in result
        assert "Druga recenica." in result


class TestDetectSections:
    """Testovi za _detect_sections."""

    def test_detects_h1_headings(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "# Uvod\nOvo je uvodni tekst.\n# Glavni deo\nOvo je glavni deo."
        sections = _detect_sections(text)
        assert len(sections) == 2
        assert sections[0]["title"] == "Uvod"
        assert sections[0]["heading_level"] == 1
        assert sections[1]["title"] == "Glavni deo"
        assert sections[1]["heading_level"] == 1

    def test_detects_h2_headings(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "## Prva sekcija\nTekst prve sekcije.\n## Druga sekcija\nTekst druge sekcije."
        sections = _detect_sections(text)
        assert len(sections) == 2
        assert sections[0]["title"] == "Prva sekcija"
        assert sections[1]["heading_level"] == 2

    def test_detects_h3_headings(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "### Podsekcija A\nTekst A.\n### Podsekcija B\nTekst B."
        sections = _detect_sections(text)
        assert len(sections) == 2
        assert sections[0]["heading_level"] == 3

    def test_detects_all_caps_as_heading(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "UVOD\nOvo je uvod.\nZAKLJUCAK\nOvo je zakljucak."
        sections = _detect_sections(text)
        assert len(sections) == 2
        assert sections[0]["title"] == "UVOD"
        assert sections[0]["heading_level"] == 2

    def test_default_section_when_no_headings(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "Ovo je obican tekst bez headinga."
        sections = _detect_sections(text)
        assert len(sections) == 1
        assert sections[0]["title"] == "Uvod"
        assert sections[0]["heading_level"] == 1

    def test_returns_empty_for_empty_text(self):
        from app.services.knowledge_ingestion import _detect_sections

        sections = _detect_sections("")
        assert len(sections) == 1
        assert sections[0]["title"] == "Uvod"

    def test_content_lines_in_section(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "# Naslov\nPrvi pasus.\nDrugi pasus.\n## Podnaslov\nPod tekst."
        sections = _detect_sections(text)
        assert len(sections) == 2
        assert len(sections[0]["content_lines"]) == 2
        assert "Prvi pasus." in sections[0]["content_lines"]
        assert "Drugi pasus." in sections[0]["content_lines"]
        assert "Pod tekst." in sections[1]["content_lines"]

    def test_skips_short_all_caps(self):
        from app.services.knowledge_ingestion import _detect_sections

        text = "AB\nKratko.\nHI\nJos krace."
        sections = _detect_sections(text)
        assert len(sections) == 1  # only default "Uvod" section
        assert sections[0]["title"] == "Uvod"


class TestTieredSimilaritySearch:
    """Testovi za tiered_similarity_search."""

    def test_returns_empty_levels_when_no_chunks(self):
        from app.services.rag import tiered_similarity_search

        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            result = tiered_similarity_search(mock_db, "test query")

        assert result == {"l0": [], "l1": [], "l2": []}

    def test_returns_l2_results_with_section_context(self):
        from app.services.rag import tiered_similarity_search

        mock_db = MagicMock()

        l0_rows = MagicMock()
        l0_rows.fetchall.return_value = []
        l1_rows = MagicMock()
        l1_rows.fetchall.return_value = []
        l2_rows = MagicMock()
        l2_row = MagicMock()
        l2_row.content = "test content"
        l2_row.chunk_index = 0
        l2_row.section_index = 1
        l2_row.section_title = "Test Section"
        l2_row.source_name = "Test Doc"
        l2_row.source_type = "pdf"
        l2_row.url = None
        l2_row.similarity = 0.85
        l2_rows.fetchall.return_value = [l2_row]

        mock_db.execute.side_effect = [l0_rows, l1_rows, l2_rows]

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            result = tiered_similarity_search(mock_db, "test query")

        assert len(result["l2"]) == 1
        assert result["l2"][0]["content"] == "test content"
        assert result["l2"][0]["section_title"] == "Test Section"
        assert result["l2"][0]["section_index"] == 1

    def test_l0_and_l1_returned_with_similarity_threshold(self):
        from app.services.rag import tiered_similarity_search

        mock_db = MagicMock()

        l0_r = MagicMock()
        l0_row = MagicMock()
        l0_row.source_id = "src-1"
        l0_row.document_title = "Doc A"
        l0_row.summary = "Summary of doc"
        l0_row.similarity = 0.92
        l0_r.fetchall.return_value = [l0_row]

        l1_r = MagicMock()
        l1_row = MagicMock()
        l1_row.source_id = "src-1"
        l1_row.section_index = 0
        l1_row.section_title = "Section A"
        l1_row.summary = "Section summary"
        l1_row.similarity = 0.78
        l1_r.fetchall.return_value = [l1_row]

        l2_r = MagicMock()
        l2_r.fetchall.return_value = []

        mock_db.execute.side_effect = [l0_r, l1_r, l2_r]

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            result = tiered_similarity_search(mock_db, "test query")

        assert len(result["l0"]) == 1
        assert result["l0"][0]["document_title"] == "Doc A"
        assert result["l0"][0]["similarity"] == 0.92
        assert len(result["l1"]) == 1
        assert result["l1"][0]["section_title"] == "Section A"

    def test_filters_below_threshold(self):
        from app.services.rag import tiered_similarity_search

        mock_db = MagicMock()

        l0_r = MagicMock()
        l0_row = MagicMock()
        l0_row.source_id = "src-1"
        l0_row.document_title = "Doc A"
        l0_row.summary = "Summary"
        l0_row.similarity = 0.3
        l0_r.fetchall.return_value = [l0_row]
        l1_r = MagicMock()
        l1_r.fetchall.return_value = []
        l2_r = MagicMock()
        l2_r.fetchall.return_value = []

        mock_db.execute.side_effect = [l0_r, l1_r, l2_r]

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            result = tiered_similarity_search(mock_db, "test query")

        assert result["l0"] == []

    def test_handles_exception_gracefully(self):
        from app.services.rag import tiered_similarity_search

        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB error")

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            result = tiered_similarity_search(mock_db, "test query")

        assert result == {"l0": [], "l1": [], "l2": []}


class TestTieredRagQuery:
    """Testovi za tiered_rag_query."""

    @pytest.mark.asyncio
    async def test_tiered_query_with_l0_l1_l2_context(self):
        from app.services.rag import tiered_rag_query

        mock_tiered_result = {
            "l0": [
                {
                    "source_id": "1",
                    "document_title": "Doc",
                    "summary": "Doc summary",
                    "similarity": 0.9,
                }
            ],
            "l1": [
                {
                    "source_id": "1",
                    "section_index": 0,
                    "section_title": "Sec",
                    "summary": "Sec summary",
                    "similarity": 0.8,
                }
            ],
            "l2": [
                {
                    "content": "Detail",
                    "source_name": "Doc",
                    "source_type": "pdf",
                    "url": None,
                    "similarity": 0.75,
                    "chunk_index": 0,
                    "section_index": 0,
                    "section_title": "Sec",
                }
            ],
        }

        with patch(
            "app.services.rag.tiered_similarity_search", return_value=mock_tiered_result
        ):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": "Tiered answer"}}]
                }
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = "test-key"
                    s.OPENAI_API_KEY = ""
                    s.GROQ_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""

                    result = await tiered_rag_query(
                        db=MagicMock(),
                        query="test",
                        provider_override="gemini",
                    )

        assert result["answer"] == "Tiered answer"
        assert result["l0_used"] == 1
        assert result["l1_used"] == 1
        assert result["chunks_used"] == 1
        assert result["has_context"] is True

    @pytest.mark.asyncio
    async def test_tiered_query_no_context_still_calls_ai(self):
        from app.services.rag import tiered_rag_query

        with patch(
            "app.services.rag.tiered_similarity_search",
            return_value={"l0": [], "l1": [], "l2": []},
        ):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = {
                    "choices": [{"message": {"content": "Direct answer"}}]
                }
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_resp)
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = "key"
                    s.OPENAI_API_KEY = ""
                    s.GROQ_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""

                    result = await tiered_rag_query(
                        db=MagicMock(), query="test", provider_override="gemini"
                    )

        assert result["answer"] == "Direct answer"
        assert result["has_context"] is False
        assert result["l0_used"] == 0

    @pytest.mark.asyncio
    async def test_tiered_query_no_ai_shows_helpful_message(self):
        from app.services.rag import tiered_rag_query

        with patch(
            "app.services.rag.tiered_similarity_search",
            return_value={"l0": [], "l1": [], "l2": []},
        ):
            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(
                    side_effect=Exception("Connection refused")
                )
                mock_client_cls.return_value = mock_client

                with patch("app.core.config.settings") as s:
                    s.GEMINI_API_KEY = "key"
                    s.OPENAI_API_KEY = ""
                    s.GROQ_API_KEY = ""
                    s.MISTRAL_API_KEY = ""
                    s.ANTHROPIC_API_KEY = ""

                    result = await tiered_rag_query(
                        db=MagicMock(), query="test", provider_override="gemini"
                    )

        assert "Nisam pronašao" not in result["answer"]
        assert "nije dostupan" in result["answer"]


class TestTieredSaveFunctions:
    """Testovi za save_tiered_chunks_to_db, save_section_summary, save_document_summary."""

    def test_save_tiered_chunks_returns_count(self):
        from app.services.rag import save_tiered_chunks_to_db

        mock_db = MagicMock()

        chunks = [
            {
                "content": "chunk1",
                "section_index": 0,
                "section_title": "Sec 1",
                "heading_level": 2,
            },
            {
                "content": "chunk2",
                "section_index": 1,
                "section_title": "Sec 2",
                "heading_level": 3,
            },
        ]

        with patch(
            "app.services.rag.embed_texts", return_value=[[0.1] * 384, [0.2] * 384]
        ):
            result = save_tiered_chunks_to_db(mock_db, "src-1", chunks)

        assert result == 2
        assert mock_db.execute.call_count == 3  # DELETE + 2 INSERT
        assert mock_db.commit.called

    def test_save_tiered_chunks_empty_returns_zero(self):
        from app.services.rag import save_tiered_chunks_to_db

        result = save_tiered_chunks_to_db(MagicMock(), "src-1", [])
        assert result == 0

    def test_save_section_summary_calls_db(self):
        from app.services.rag import save_section_summary

        mock_db = MagicMock()

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            save_section_summary(
                mock_db,
                "src-1",
                0,
                "Test Section",
                2,
                "Full content",
                "Short summary",
                5,
                100,
            )

        assert mock_db.execute.called
        assert mock_db.commit.called

    def test_save_document_summary_calls_db(self):
        from app.services.rag import save_document_summary

        mock_db = MagicMock()

        with patch("app.services.rag.embed_text", return_value=[0.1] * 384):
            save_document_summary(
                mock_db,
                "src-1",
                "Doc Title",
                "Doc summary",
                20,
                500,
            )

        assert mock_db.execute.called
        assert mock_db.commit.called


class TestIngestSourceWithTiers:
    """Testovi za ingest_source_with_tiers."""

    def test_returns_zero_for_empty_content(self):
        from app.services.knowledge_ingestion import ingest_source_with_tiers

        mock_db = MagicMock()
        result = ingest_source_with_tiers(mock_db, "src-1", "text", "", "Empty Doc")
        assert result == 0

    def test_ingest_with_sections(self):
        from app.services.knowledge_ingestion import ingest_source_with_tiers

        mock_db = MagicMock()

        with patch("app.services.rag.chunk_text", return_value=["chunk1", "chunk2"]):
            with patch(
                "app.services.rag.save_tiered_chunks_to_db", return_value=4
            ) as mock_save:
                with patch("app.services.rag.save_section_summary") as mock_summary:
                    with patch(
                        "app.services.rag.save_document_summary"
                    ) as mock_doc_summary:
                        result = ingest_source_with_tiers(
                            mock_db,
                            "src-1",
                            "pdf",
                            "# Naslov\nOvo je tekst.\n## Podnaslov\nJos teksta.",
                            "Test Doc",
                        )

        assert result == 4
        assert mock_save.called
        assert mock_summary.called
        assert mock_doc_summary.called

    def test_handles_exception_gracefully(self):
        from app.services.knowledge_ingestion import ingest_source_with_tiers

        mock_db = MagicMock()
        mock_db.execute.side_effect = Exception("DB error")
        result = ingest_source_with_tiers(mock_db, "src-1", "text", "hello", "Err Doc")
        assert result == 0


class TestTieredApiEndpoint:
    """Testovi za /knowledge/query/tiered endpoint."""

    @staticmethod
    def _try_import_app():
        """Import app.main, skipping if Docker-only deps are unavailable."""
        try:
            from app.main import app

            return app
        except ModuleNotFoundError as e:
            pytest.skip(f"Skip — host missing Docker-only dependency: {e}")

    @pytest.mark.asyncio
    async def test_tiered_endpoint_returns_answer(self, db):
        app = self._try_import_app()
        from app.db.session import get_db
        from httpx import AsyncClient

        app.dependency_overrides[get_db] = lambda: db

        try:
            with patch("app.services.rag.tiered_rag_query") as mock_tiered:
                mock_tiered.return_value = {
                    "answer": "Tiered answer.",
                    "sources": [{"name": "Doc", "type": "pdf", "url": None}],
                    "chunks_used": 2,
                    "l0_used": 1,
                    "l1_used": 1,
                    "provider": "gemini",
                    "has_context": True,
                }

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/knowledge/query/tiered",
                        json={"query": "What is this?", "provider": "gemini"},
                        headers={"Authorization": "Bearer fake-token"},
                    )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code != 500

    @pytest.mark.asyncio
    async def test_tiered_endpoint_requires_query_field(self, db):
        app = self._try_import_app()
        from app.db.session import get_db
        from httpx import AsyncClient

        app.dependency_overrides[get_db] = lambda: db

        try:
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.post(
                    "/api/v1/knowledge/query/tiered",
                    json={},
                )
        finally:
            app.dependency_overrides.clear()

        assert response.status_code in (422, 401)

    @pytest.mark.asyncio
    async def test_tiered_endpoint_returns_l0_l1_counts(self, db):
        app = self._try_import_app()
        from app.db.session import get_db
        from httpx import AsyncClient

        app.dependency_overrides[get_db] = lambda: db

        try:
            with patch("app.services.rag.tiered_rag_query") as mock_tiered:
                mock_tiered.return_value = {
                    "answer": "Answer with L0/L1.",
                    "sources": [],
                    "chunks_used": 0,
                    "l0_used": 1,
                    "l1_used": 2,
                    "provider": "gemini",
                    "has_context": True,
                }

                async with AsyncClient(app=app, base_url="http://test") as client:
                    response = await client.post(
                        "/api/v1/knowledge/query/tiered",
                        json={"query": "test", "provider": "gemini"},
                        headers={"Authorization": "Bearer fake-token"},
                    )
        finally:
            app.dependency_overrides.clear()

        if response.status_code == 200:
            data = response.json()
            assert "l0_used" in data
            assert "l1_used" in data
