# Quiz Quality Pipeline — Rezultati

## Sta je uradjeno

Implementirane izmene za poboljsanje kvaliteta kviz pitanja — timeout konzistentnost, MC→CB konverzija, semanticka pravila u promptu, i refaktor answer checking-a.

## Izmenjeni fajlovi

| Fajl | Promena |
|------|---------|
| `backend/app/services/quiz/clients/openai.py` | `self.timeout = 120` → `self.timeout = 45` |
| `backend/app/services/quiz/clients/claude.py` | `self.timeout = 120` → `self.timeout = 45` |
| `backend/app/services/quiz/clients/openai_compat.py` | `self.timeout = 120` → `self.timeout = 45` |
| `backend/app/workers/tasks/quiz.py` | Dodato `soft_time_limit=300, time_limit=360` na `@shared_task` dekoratore |
| `backend/app/services/quiz/prompts/quiz_prompt.py` | Dodata semanticka pravila za MC vs checkbox (BAD/GOOD primeri) |
| `backend/app/services/quiz/helpers/__init__.py` | MC→CB konverzija u `_validate_questions()` |
| `backend/app/services/quiz/prompts/subjects.py` | Uklonjene per-category instrukcije (svedeno na prazne stringove) |
| `backend/app/api/endpoints/quizzes.py` | `submit_attempt()` sada koristi `_check_answer_static()` |
| `backend/app/services/quiz/generation.py` | **NOVI** — `PER_PROVIDER_TIMEOUT=45` + `generate_with_prompt()` |
| `backend/app/tests/unit/test_generation.py` | **NOVI** — 6 timeout testova |
| `backend/app/tests/unit/test_quiz_service.py` | Dodato 15 testova (7 prompt semantika + 8 MC→CB validacija) |
| `backend/app/tests/integration/test_quiz.py` | Dodata `TestSubmitAttemptAPI` klasa sa 6 testova |
| `AGENTS.md` | Azuriran sa FAZA E sekcijom i POSLEDNJI UPDATE unosom |

## Rezultat

- 27 novih testova (6 + 15 + 6)
- MC→CB auto-konverzija kad su sve opcije tacne
- Semanticka pravila u promptu sprecavaju AI da generise pogresne tipove
- Konzistentan 45s timeout za sve provajdere
- `_check_answer_static` se koristi i u API i u testovima
- 3 fajla sa smanjenim timeout-om (120s → 45s)
- 2 Celery taska sa `soft_time_limit=300`

## Branch

- `feature/quiz-quality-pipeline`
- PR #1
- Base: `origin/main` (`a8e47c6`)
