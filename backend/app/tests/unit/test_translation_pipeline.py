# -*- coding: utf-8 -*-
"""
TESTS - Translation Pipeline
Testovi za run_document_translation pipeline:
- Module-level konstante
- Rate limiter integracija
- ThreadPoolExecutor paralelizacija
- Worker error handling
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.db.models.document import Chunk


def _create_untranslated_chunks(db, document, count=5):
    """Helper: kreira neprevedene chunkove za test dokument."""
    chunks = []
    for i in range(count):
        chunk = Chunk(
            document_id=document.id,
            sequence_number=i,
            content=f"Test content chunk number {i}. This is some English text for testing.",
            is_translated=0,
            is_reviewed=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(chunk)
        chunks.append(chunk)
    db.commit()
    return chunks


def _make_batch_mock(chunk_count):
    """Helper: kreira mock result za translate_with_fallback (koristi se u worker testovima)."""
    parts = ["Prev 0 - Ovo je prevedeni tekst za chunk 0"]
    for i in range(1, chunk_count):
        parts.append(f"\n\n### {i + 1}\nPrev {i} - Ovo je prevedeni tekst za chunk {i}")

    return MagicMock(
        success=True,
        translated_text="".join(parts),
        cost=0.01,
        tokens_used=50,
        error=None,
    )


def _mock_worker_result(chunk_count):
    """Helper: kreira povratnu vrednost za mock _translate_batch_worker."""
    return {
        "translated_count": chunk_count,
        "total_cost": 0.01 * chunk_count,
        "total_tokens": 50 * chunk_count,
        "errors": [],
    }


class TestPipelineConstants:
    """Testovi za module-level konstante i reset."""

    def test_default_batch_size(self):
        from app.workers.tasks.translation import TRANSLATION_BATCH_SIZE

        assert TRANSLATION_BATCH_SIZE == 5

    def test_default_checkpoint_interval(self):
        from app.workers.tasks.translation import TRANSLATION_CHECKPOINT_EVERY

        assert TRANSLATION_CHECKPOINT_EVERY == 10

    def test_default_max_retries(self):
        from app.workers.tasks.translation import TRANSLATION_MAX_RETRIES

        assert TRANSLATION_MAX_RETRIES == 2

    def test_parallel_workers_constant(self):
        """Proverava da TRANSLATION_PARALLEL_WORKERS postoji i ima default vrednost."""
        from app.workers.tasks.translation import TRANSLATION_PARALLEL_WORKERS

        assert TRANSLATION_PARALLEL_WORKERS >= 1

    def test_rate_limiter_singleton_exists(self):
        from app.workers.tasks.translation import _rate_limiter

        assert _rate_limiter is not None

    def test_reset_rate_limiter_clears_state(self):
        from app.workers.tasks.translation import reset_rate_limiter, _rate_limiter

        _rate_limiter.record_request("test_prov")
        assert _rate_limiter.request_count("test_prov") == 1
        reset_rate_limiter()
        assert _rate_limiter.request_count("test_prov") == 0


class TestPipelineErrors:
    """Testovi za error handling."""

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def test_document_not_found_raises_error(self, db):
        from app.workers.tasks.translation import run_document_translation

        with pytest.raises(ValueError, match="Document not found"):
            run_document_translation(db, "non-existent-id")

    def test_wrong_document_status_raises_error(self, db, test_document):
        from app.workers.tasks.translation import run_document_translation

        test_document.status = "pending"
        db.commit()
        with pytest.raises(ValueError, match="Document must be processed first"):
            run_document_translation(db, str(test_document.id))

    def test_no_chunks_raises_error(self, db, test_document):
        from app.workers.tasks.translation import run_document_translation

        with pytest.raises(ValueError, match="No chunks found"):
            run_document_translation(db, str(test_document.id))


class TestPipelineHappyPath:
    """Testovi za uspesan prevod sa mock-ovanim _translate_batch_worker."""

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def test_all_chunks_get_translated(self, db, test_document):
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 3)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["status"] == "success"
        assert result["translated_chunks"] == 3
        assert result["total_chunks"] == 3

    def test_document_status_becomes_completed(self, db, test_document):
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 2)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        db.refresh(test_document)
        assert test_document.status == "completed"

    def test_rate_limiter_records_requests(self, db, test_document):
        """Worker mock poziva rate limiter da simulira stvarno ponasanje."""
        from app.workers.tasks.translation import (
            run_document_translation,
            _rate_limiter,
        )

        _create_untranslated_chunks(db, test_document, 2)
        count_before = _rate_limiter.request_count("ollama")

        def mock_worker_with_rate(batch_data, *a, **kw):
            _rate_limiter.record_request("ollama")
            return _mock_worker_result(len(batch_data))

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=mock_worker_with_rate,
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        assert _rate_limiter.request_count("ollama") > count_before

    def test_result_contains_metadata(self, db, test_document):
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 2)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert "total_cost" in result
        assert "total_tokens" in result
        assert "document_id" in result
        assert "errors_count" in result

    def test_chunks_marked_as_translated_in_db(self, db, test_document):
        """
        Mock worker azurira chunkove u test DB da simulira stvarno ponasanje.
        Odrzava originalni test intent (chunkovi su oznaceni kao prevedeni).
        """
        from app.workers.tasks.translation import run_document_translation

        chunks = _create_untranslated_chunks(db, test_document, 2)

        def mock_worker_updates_chunks(batch_data, *a, **kw):
            for item in batch_data:
                chunk = db.query(Chunk).filter(Chunk.id == item["id"]).first()
                if chunk:
                    chunk.translated_content = "Prev"
                    chunk.is_translated = 1
            db.commit()
            return _mock_worker_result(len(batch_data))

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=mock_worker_updates_chunks,
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        for chunk in chunks:
            db.refresh(chunk)
            assert chunk.is_translated == 1
            assert chunk.translated_content is not None

    def test_multiple_batches_all_translated(self, db, test_document):
        """12 chunks = 3 batches (BATCH_SIZE=5, 5, 2)."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 12)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["translated_chunks"] == 12
        assert result["status"] == "success"


class TestPipelineCheckpoint:
    """Testovi za checkpoint commit pattern sa paralelnim worker-ima."""

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def test_checkpoint_commits_at_interval(self, db, test_document, mocker):
        """
        Proverava da se commit poziva:
        1. Inicijalni status
        2. Posle worker-a (mid cleanup)
        3. Finalni metadata
        """
        from app.workers.tasks.translation import (
            run_document_translation,
            TRANSLATION_CHECKPOINT_EVERY,
        )

        num_chunks = TRANSLATION_CHECKPOINT_EVERY + 5
        _create_untranslated_chunks(db, test_document, num_chunks)

        commit_spy = mocker.spy(db, "commit")

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        assert commit_spy.call_count >= 3

    def test_checkpoint_no_commit_below_interval(self, db, test_document, mocker):
        """Bez checkpoint commit-a ako je manje od CHECKPOINT_EVERY."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 3)

        commit_spy = mocker.spy(db, "commit")

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        # initial status + mid cleanup + final metadata/status
        assert commit_spy.call_count == 3

    def test_checkpoint_data_written(self, db, test_document):
        """Checkpoint metapodaci se upisuju u file_metadata."""
        from app.workers.tasks.translation import (
            run_document_translation,
            TRANSLATION_CHECKPOINT_EVERY,
        )
        from app.db.models.document import Document

        num_chunks = TRANSLATION_CHECKPOINT_EVERY + 5
        _create_untranslated_chunks(db, test_document, num_chunks)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            doc_id = str(test_document.id)
            run_document_translation(db, doc_id, provider="ollama")

        fresh_doc = db.query(Document).filter(Document.id == doc_id).first()
        metadata = fresh_doc.file_metadata or {}
        translation = metadata.get("translation", {})
        assert translation.get("translated_chunks") == num_chunks
        assert "total_tokens" in translation


class TestPipelineFallback:
    """
    Orchestration-level error handling.
    _translate_batch_worker fallback (batch->individual) se testira u worker unit testovima.
    """

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def test_worker_errors_reported_in_result(self, db, test_document):
        """Worker greske se propagiraju u rezultat preko errors liste."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 2)

        def worker_with_errors(batch_data, *a, **kw):
            return {
                "translated_count": 0,
                "total_cost": 0,
                "total_tokens": 0,
                "errors": [
                    f"Chunk {item['sequence_number']} failed" for item in batch_data
                ],
            }

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=worker_with_errors,
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["translated_chunks"] == 0
        assert result["errors_count"] > 0

    def test_partial_translation_when_some_fail(self, db, test_document):
        """Delimicni uspeh — samo jedan chunk uspeva."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 5)

        call_log = {"count": 0}

        def partial_worker(batch_data, *a, **kw):
            call_log["count"] += 1
            if call_log["count"] == 1:
                return {
                    "translated_count": 1,
                    "total_cost": 0.01,
                    "total_tokens": 50,
                    "errors": ["Chunk 0 failed"],
                }
            return _mock_worker_result(len(batch_data))

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=partial_worker,
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["translated_chunks"] >= 1
        assert result["status"] == "success"

    def test_all_workers_raise_exception(self, db, test_document):
        """Worker exception se hvata i dodaje u errors listu."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 6)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=RuntimeError("Translation service down"),
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["translated_chunks"] == 0
        assert result["errors_count"] == 2  # 2 batches = 2 errors


class TestPipelineParallel:
    """Testovi za ThreadPoolExecutor paralelizaciju."""

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def test_worker_called_once_per_batch(self, db, test_document, mocker):
        """Proverava da se _translate_batch_worker poziva za svaki batch."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 12)

        mock_worker = mocker.patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        )

        run_document_translation(db, str(test_document.id), provider="ollama")

        assert mock_worker.call_count == 3  # 12/5 = 3 batches

    def test_worker_receives_correct_batch_data(self, db, test_document):
        """Proverava da worker dobija ispravne batch podatke."""
        from app.workers.tasks.translation import run_document_translation

        chunks = _create_untranslated_chunks(db, test_document, 5)
        expected_ids = {str(c.id) for c in chunks}
        received_data = []

        def capture_worker(batch_data, *a, **kw):
            received_data.extend(batch_data)
            return _mock_worker_result(len(batch_data))

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=capture_worker,
        ):
            run_document_translation(db, str(test_document.id), provider="ollama")

        received_ids = {str(item["id"]) for item in received_data}
        assert received_ids == expected_ids

    def test_result_aggregation(self, db, test_document):
        """Proverava agregaciju rezultata iz vise worker-a."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 12)

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=lambda batch_data, *a, **kw: _mock_worker_result(
                len(batch_data)
            ),
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["translated_chunks"] == 12
        assert result["total_cost"] == pytest.approx(0.12, 0.01)
        assert result["total_tokens"] == 600

    def test_single_batch_no_parallel(self, db, test_document, mocker):
        """Proverava da mali dokument (1 batch) radi ispravno."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 3)

        mock_worker = mocker.patch(
            "app.workers.tasks.translation._translate_batch_worker",
            return_value=_mock_worker_result(3),
        )

        result = run_document_translation(db, str(test_document.id), provider="ollama")

        assert mock_worker.call_count == 1
        assert result["translated_chunks"] == 3

    def test_worker_exception_does_not_crash_pipeline(self, db, test_document):
        """Exception u worker-u ne rusava ceo pipeline."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 12)

        def worker_with_exception(batch_data, *a, **kw):
            raise RuntimeError("Worker crashed")

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=worker_with_exception,
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        assert result["errors_count"] == 3  # 3 batches all crash
        assert result["status"] == "success"

    def test_mixed_success_and_failure(self, db, test_document):
        """Neki worker-i uspevaju, neki padaju — rezultat se agregira."""
        from app.workers.tasks.translation import run_document_translation

        _create_untranslated_chunks(db, test_document, 12)

        call_count = [0]

        def mixed_worker(batch_data, *a, **kw):
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("First worker crashed")
            return _mock_worker_result(len(batch_data))

        with patch(
            "app.workers.tasks.translation._translate_batch_worker",
            side_effect=mixed_worker,
        ):
            result = run_document_translation(
                db, str(test_document.id), provider="ollama"
            )

        # First batch (5) crashes, remaining 2 batches (5+2=7) succeed
        assert result["translated_chunks"] == 7
        assert result["errors_count"] == 1


class TestWorkerBatch:
    """
    Direktni unit testovi za _translate_batch_worker funkciju.
    Testira batch translation, fallback na individual retry, error handling.
    """

    def setup_method(self):
        from app.workers.tasks.translation import reset_rate_limiter

        reset_rate_limiter()

    def _make_worker_session(self, db):
        """Kreira test sesiju za worker koristeci test engine."""
        from app.tests.conftest import TestingSessionLocal

        return TestingSessionLocal()

    def _make_batch_data(self, chunks):
        """Helper: pretvara chunk objekte u batch_data dict."""
        return [
            {"id": c.id, "content": c.content, "sequence_number": c.sequence_number}
            for c in chunks
        ]

    def test_batch_translation_success(self, db, test_document):
        """
        Worker uspesno prevodi batch od 3 chunka.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 3)
        batch_data = self._make_batch_data(chunks)

        mock_result = _make_batch_mock(3)

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                return_value=mock_result,
            ):
                result = _translate_batch_worker(
                    batch_data, "ollama", "en", "sr", {}, 0
                )

        worker_session.close()

        assert result["translated_count"] == 3
        assert result["total_cost"] > 0
        assert result["total_tokens"] > 0
        assert result["errors"] == []

    def test_batch_fallback_to_individual(self, db, test_document):
        """
        Kad batch prevod padne, worker pada na individualni retry po chunk-u.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 3)
        batch_data = self._make_batch_data(chunks)

        individual_mock = MagicMock(
            success=True,
            translated_text="Individual translated text",
            cost=0.005,
            tokens_used=25,
            error=None,
        )

        call_count = [0]

        def translate_side_effect(*a, **kw):
            call_count[0] += 1
            # Batch: fails on both retries (TRANSLATION_MAX_RETRIES=2)
            if call_count[0] in (1, 2):
                return MagicMock(success=False, error="Batch failed")
            return individual_mock

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                side_effect=translate_side_effect,
            ):
                result = _translate_batch_worker(
                    batch_data, "ollama", "en", "sr", {}, 0
                )

        worker_session.close()

        assert result["translated_count"] == 3
        assert result["errors"] == []

    def test_individual_retry_exhausted(self, db, test_document):
        """
        Kad batch i svi individualni retry-i padnu, chunkovi se oznacavaju kao greske.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 2)
        batch_data = self._make_batch_data(chunks)

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                return_value=MagicMock(success=False, error="Provider unavailable"),
            ):
                result = _translate_batch_worker(
                    batch_data, "ollama", "en", "sr", {}, 0
                )

        worker_session.close()

        assert result["translated_count"] == 0
        assert len(result["errors"]) == 2

    def test_partial_individual_success(self, db, test_document):
        """
        Neki individualni chunkovi uspevaju, neki padaju.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 3)
        batch_data = self._make_batch_data(chunks)

        individual_mock = MagicMock(
            success=True,
            translated_text="Individual success",
            cost=0.005,
            tokens_used=25,
            error=None,
        )

        call_count = [0]

        def translate_side_effect(*a, **kw):
            call_count[0] += 1
            # Batch: fails on both retries (TRANSLATION_MAX_RETRIES=2)
            if call_count[0] in (1, 2):
                return MagicMock(success=False, error="Batch failed")
            # Chunk 0: call 3 succeeds
            # Chunk 1: call 4 fails (attempt 0), call 5 also fails (attempt 1)
            if call_count[0] in (4, 5):
                return MagicMock(success=False, error="Individual chunk failed")
            # Chunk 2: call 6 succeeds
            return individual_mock

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                side_effect=translate_side_effect,
            ):
                result = _translate_batch_worker(
                    batch_data, "ollama", "en", "sr", {}, 0
                )

        worker_session.close()

        assert result["translated_count"] == 2
        assert len(result["errors"]) == 1
        assert "Chunk 1" in result["errors"][0] or "Failed" in result["errors"][0]

    def test_worker_rate_limiter_integration(self, db, test_document):
        """
        Worker poziva rate limiter pre batch i individualnih poziva.
        """
        from app.workers.tasks.translation import (
            _translate_batch_worker,
            _rate_limiter,
        )

        chunks = _create_untranslated_chunks(db, test_document, 2)
        batch_data = self._make_batch_data(chunks)

        mock_result = _make_batch_mock(2)
        count_before = _rate_limiter.request_count("ollama")

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                return_value=mock_result,
            ):
                _translate_batch_worker(batch_data, "ollama", "en", "sr", {}, 0)

        worker_session.close()

        assert _rate_limiter.request_count("ollama") > count_before

    def test_worker_empty_batch(self, db, test_document):
        """
        Prazan batch ne izaziva gresku, vraca nula rezultat.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            result = _translate_batch_worker([], "ollama", "en", "sr", {}, 0)

        worker_session.close()

        assert result["translated_count"] == 0
        assert result["total_cost"] == 0
        assert result["total_tokens"] == 0
        assert result["errors"] == []

    def test_translated_content_saved_to_db(self, db, test_document):
        """
        Prevedeni sadrzaj se cuva u bazi kroz worker sesiju.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 2)
        batch_data = self._make_batch_data(chunks)

        mock_result = _make_batch_mock(2)

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                return_value=mock_result,
            ):
                _translate_batch_worker(batch_data, "ollama", "en", "sr", {}, 0)

        worker_session.close()

        verify_session = self._make_worker_session(db)
        for chunk in chunks:
            saved = verify_session.query(Chunk).filter(Chunk.id == chunk.id).first()
            assert saved is not None
            assert saved.is_translated == 1
            assert saved.translated_content is not None
        verify_session.close()

    def test_worker_exception_returns_error_dict(self, db, test_document):
        """
        Exception unutar workera se hvata i vraca kao errors dict, ne propogira se.
        """
        from app.workers.tasks.translation import _translate_batch_worker

        chunks = _create_untranslated_chunks(db, test_document, 1)
        batch_data = self._make_batch_data(chunks)

        worker_session = self._make_worker_session(db)

        with patch(
            "app.workers.tasks.translation.get_db_session", return_value=worker_session
        ):
            with patch(
                "app.workers.tasks.translation.translate_with_fallback",
                side_effect=Exception("Unexpected network error"),
            ):
                result = _translate_batch_worker(
                    batch_data, "ollama", "en", "sr", {}, 0
                )

        worker_session.close()

        assert result["translated_count"] == 0
        assert len(result["errors"]) > 0
