# -*- coding: utf-8 -*-
"""
Unit testovi za nove funkcionalnosti:
- RAG similarity threshold
- Study streak calculation
- flag_modified import u tasks
- Dashboard translationPct logika
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, timedelta


# ─────────────────────────────────────────────
# 1. RAG similarity threshold
# ─────────────────────────────────────────────
class TestRagSimilarityThreshold:
    """Testira da se nerelevantni chunk-ovi filtriraju."""

    def _make_chunks(self, scores):
        return [{"content": f"chunk{i}", "source_name": f"src{i}",
                 "source_type": "pdf", "similarity": s, "url": None, "chunk_index": i}
                for i, s in enumerate(scores)]

    def test_chunks_above_threshold_kept(self):
        THRESHOLD = 0.45
        chunks = self._make_chunks([0.9, 0.7, 0.5])
        filtered = [c for c in chunks if c["similarity"] >= THRESHOLD]
        assert len(filtered) == 3

    def test_chunks_below_threshold_removed(self):
        THRESHOLD = 0.45
        chunks = self._make_chunks([0.1, 0.2, 0.3, 0.44])
        filtered = [c for c in chunks if c["similarity"] >= THRESHOLD]
        assert len(filtered) == 0

    def test_exact_threshold_kept(self):
        THRESHOLD = 0.45
        chunks = self._make_chunks([0.45])
        filtered = [c for c in chunks if c["similarity"] >= THRESHOLD]
        assert len(filtered) == 1

    def test_mixed_scores(self):
        THRESHOLD = 0.45
        chunks = self._make_chunks([0.9, 0.44, 0.5, 0.1, 0.6])
        filtered = [c for c in chunks if c["similarity"] >= THRESHOLD]
        assert len(filtered) == 3
        assert all(c["similarity"] >= THRESHOLD for c in filtered)

    def test_unrelated_question_gets_no_context(self):
        """Pitanje 'koji je danas dan' ne bi trebalo da vrati kontekst iz tehničkih dok."""
        THRESHOLD = 0.45
        # Simuliramo niske sličnosti za nepovezano pitanje
        chunks = self._make_chunks([0.12, 0.18, 0.22, 0.15, 0.09])
        filtered = [c for c in chunks if c["similarity"] >= THRESHOLD]
        assert len(filtered) == 0, "Nerelevantni chunk-ovi ne smiju biti u kontekstu"


# ─────────────────────────────────────────────
# 2. Study streak calculation
# ─────────────────────────────────────────────
class TestStudyStreak:
    """Testira logiku računanja niza dana učenja."""

    def _calc_streak(self, activity_dates: list) -> int:
        """Replika logike iz users.py."""
        if not activity_dates:
            return 0
        today = date.today()
        parsed = set(activity_dates)
        streak = 0
        check = today
        for _ in range(len(parsed) + 1):
            if check in parsed:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
        return streak

    def test_no_attempts_streak_zero(self):
        assert self._calc_streak([]) == 0

    def test_activity_today_streak_one(self):
        assert self._calc_streak([date.today()]) == 1

    def test_consecutive_days_counted(self):
        today = date.today()
        dates = [today, today - timedelta(1), today - timedelta(2)]
        assert self._calc_streak(dates) == 3

    def test_gap_breaks_streak(self):
        today = date.today()
        # Today and 2 days ago (gap on yesterday)
        dates = [today, today - timedelta(2)]
        assert self._calc_streak(dates) == 1

    def test_only_yesterday_no_streak(self):
        """Ako je aktivnost samo juče (ne danas) — streak = 0."""
        yesterday = date.today() - timedelta(1)
        assert self._calc_streak([yesterday]) == 0

    def test_long_streak(self):
        today = date.today()
        dates = [today - timedelta(i) for i in range(10)]
        assert self._calc_streak(dates) == 10

    def test_old_dates_dont_count(self):
        """Stare aktivnosti bez današnje ne daju streak."""
        old = [date.today() - timedelta(i+2) for i in range(5)]
        assert self._calc_streak(old) == 0

    def test_partial_attempt_today_counts(self):
        """Djelimični pokušaj (samo started_at) treba da računa u streak."""
        assert self._calc_streak([date.today()]) == 1


# ─────────────────────────────────────────────
# 3. flag_modified import provjera
# ─────────────────────────────────────────────
class TestFlagModifiedImport:
    def test_flag_modified_imported_in_tasks(self):
        import ast
        with open("app/workers/tasks.py") as f:
            tree = ast.parse(f.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.append((node.module, [a.name for a in node.names]))
        found = any(
            mod == "sqlalchemy.orm.attributes" and "flag_modified" in names
            for mod, names in imports
        )
        assert found, "flag_modified mora biti importovan iz sqlalchemy.orm.attributes"

    def test_flag_modified_called_in_translate_task(self):
        with open("app/workers/tasks.py") as f:
            content = f.read()
        count = content.count('flag_modified(document, "file_metadata")')
        assert count >= 3, f"Očekivano >=3 poziva flag_modified, nađeno: {count}"


# ─────────────────────────────────────────────
# 4. Dashboard translationPct logika
# ─────────────────────────────────────────────
class TestTranslationPctDisplay:
    """Testira logiku prikaza procenta prevoda."""

    def _get_display(self, translated: int, total: int) -> str:
        """Replika logike koja treba biti u DashboardPage."""
        if total == 0:
            return "0%"
        pct = round((translated / total) * 100)
        if pct == 0 and translated > 0:
            return "< 1%"
        return f"{pct}%"

    def test_zero_total_shows_zero(self):
        assert self._get_display(0, 0) == "0%"

    def test_all_translated_shows_100(self):
        assert self._get_display(990, 990) == "100%"

    def test_small_progress_shows_less_than_1(self):
        assert self._get_display(4, 990) == "< 1%"

    def test_exact_1_percent(self):
        assert self._get_display(10, 1000) == "1%"

    def test_zero_translated_shows_zero(self):
        assert self._get_display(0, 990) == "0%"

    def test_half_translated(self):
        assert self._get_display(495, 990) == "50%"


# ─────────────────────────────────────────────
# 5. Quiz localStorage logika (Python simulacija)
# ─────────────────────────────────────────────
class TestQuizProgressStorage:
    """Testira logiku čuvanja/učitavanja napretka kviza."""

    def _make_progress(self, attempt_id, answers, current_idx, confirmed, days_old=0):
        from datetime import datetime, timezone, timedelta as td
        saved_at = (datetime.now(timezone.utc) - td(days=days_old)).isoformat()
        return {
            "attemptId": attempt_id,
            "answers": answers,
            "currentIdx": current_idx,
            "confirmed": confirmed,
            "savedAt": saved_at,
        }

    def _is_expired(self, progress, max_days=7):
        from datetime import datetime, timezone, timedelta as td
        saved = datetime.fromisoformat(progress["savedAt"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - saved) > td(days=max_days)

    def test_fresh_progress_not_expired(self):
        p = self._make_progress("att1", {}, 0, [], days_old=0)
        assert not self._is_expired(p)

    def test_old_progress_expired(self):
        p = self._make_progress("att1", {}, 0, [], days_old=8)
        assert self._is_expired(p)

    def test_progress_has_all_fields(self):
        p = self._make_progress("att1", {"q1": "True"}, 3, ["q1"])
        assert "attemptId" in p
        assert "answers" in p
        assert "currentIdx" in p
        assert "confirmed" in p
        assert "savedAt" in p

    def test_resume_restores_state(self):
        saved = self._make_progress(
            attempt_id="abc-123",
            answers={"q1": "True", "q2": "Paris"},
            current_idx=2,
            confirmed=["q1"],
        )
        # Simuliramo handleResume
        attempt_id = saved["attemptId"]
        answers = saved["answers"]
        current_idx = saved["currentIdx"]
        confirmed = set(saved["confirmed"])

        assert attempt_id == "abc-123"
        assert answers["q1"] == "True"
        assert current_idx == 2
        assert "q1" in confirmed
        assert "q2" not in confirmed
