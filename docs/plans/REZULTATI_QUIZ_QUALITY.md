# Rezultati: Quiz Quality & Pipeline Fix (2026-06-14)

## Finalni test rezultati

| Metrika | Vrednost |
|---------|----------|
| Total tests | 819 passed, 18 skipped |
| Regresija | 0 |
| Flake8 | Clean (0 issues) |

## Izmenjeni fajlovi

| Fajl | Promena |
|------|---------|
| `backend/app/services/quiz/prompts/quiz_prompt.py` | Semanticka pravila MC vs checkbox, skracene linije za flake8 |
| `backend/app/services/quiz/helpers/__init__.py` | MC->CB correct_answer fix, checkbox validacija u sopstveni blok |
| `backend/app/services/quiz/generation.py` | `PER_PROVIDER_TIMEOUT=45`, `generate_with_prompt()` try/except |
| `backend/app/services/quiz/clients/openai.py` | timeout 120->45 |
| `backend/app/services/quiz/clients/claude.py` | timeout 120->45 |
| `backend/app/services/quiz/clients/openai_compat.py` | timeout 120->45 |
| `backend/app/workers/tasks/quiz.py` | Celery soft_time_limit+time_limit |
| `backend/app/services/quiz/prompts/subjects.py` | Uklonjene per-category tip instrukcije |

## Fiksirani bug-ovi u testovima

| Test | Problem | Fix |
|------|---------|-----|
| `test_mc_short_options_not_counted_towards_conversion` | Single-letter filter discarduje pitanje pre MC->CB logike | Opcije 'a','b','c','d' -> 'cat','dog','fox','bat' (len<=3, nisu single-letter) |
| `test_timeout_restored_on_exception` | Exception iz generate_with_prompt() propagira, timeout nije restoreovan | Dodat try/except u generate_with_prompt() |
| `test_client_without_timeout_attr` | MagicMock(spec=[]) ne dozvoljava `is_available` | `del mock_client.timeout` umesto spec |
| `test_prompt_never_creates_mc_with_all_true` | Tekst u promptu skracen | Test trazi "NEVER create multiple_choice" umesto "NEVER create a multiple_choice" |
