# Plan: Poboljšanje Kvaliteta Pitanja i Auto-Pipeline Timeout

## Pregled
Dva problema: (1) AI generiše multiple_choice pitanja gde su sve opcije tačne (treba checkbox), (2) auto-pipeline se zaglavi jer nema timeout-a na Celery taskovima i providerima.

## Architecture Decision: Universal Prompts (DISCOVERED DURING IMPLEMENTATION)

**Problem koji smo rešavali:** Kako prilagoditi tip pitanja kategoriji dokumenta (hemija→chemical_equation, IT→multiple_choice, etc.)

**Prvobitni pristup (Task 4c):** Hardkodovane instrukcije po kategoriji u `subjects.py`. Npr. "Za hemiju koristi chemical_equation", "Za IT koristi multiple_choice".

**Šta smo shvatili tokom implementacije:** Ovo je pogrešan pristup jer:
1. **Ne znamo unapred kategoriju** — korisnik uvozi bilo koji dokument, ne biramo iz padajuće liste
2. **Kategorije su preširoke** — IT dokument može imati i teorijska pitanja (gde treba checkbox) i praktična (gde treba multiple_choice)
3. **Isti dokument može imati više tipova pitanja** — ne treba cela kategorija da favorizuje jedan tip
4. **AI model treba SAM da odluči** na osnovu sadržaja, a ne na osnovu etikete

**Konačna odluka — Univerzalni prompti:**
- `quiz_prompt.py` sadrži **univerzalna semantička pravila** koja važe za SVE dokumente:
  - "Ako VIŠE opcija je tačno → checkbox. Ako SAMO JEDNA → multiple_choice."
  - Ova pravila su zasnovana na analizi sadržaja, ne na kategoriji
- `subjects.py` sadrži samo **WHAT da se pita** (formule, datumi, zakoni), ne **WHICH tip**
- **MC→CB heuristic** u `helpers/__init__.py` je druga linija odbrane — ako AI pogreši, validacija konvertuje

**Zašto je ovo ispravno:**
- Skalabilno — ne moramo da dodajemo pravila za svaku novu kategoriju
- Robustno — radi za bilo koji dokument, ne samo za prepoznate kategorije
- Profesionalno — AI model je dovoljno pametan da sam proceni na osnovu semantičkih pravila

**Verifikacija:** Ova odluka je primećena i potvrđena tokom izrade Task 1-2. Plan je ažuriran retroaktivno da reflektuje stvarni pristup.

## Root Cause Analiza

### Problem 1: Kvalitet Pitanja
- **Prompt** nema semantička pravila za izbor tipa pitanja
- **Validacija** ne detektuje multiple_choice sa svim tačnim opcijama
- **AI model** nema svest o tome kada je nešto checkbox a kada multiple_choice

### Problem 2: Auto-Pipeline Stuck
- **Celery** `generate_quiz_task` i `auto_pipeline_task` nemaju `soft_time_limit`
- **HTTP** `httpx.Client(timeout=120)` je sinhroni — blokira Celery worker
- **Fallback** petlja kroz 7 providera, svaki do 120s, ukupno do 14 min

### Problem 3: Chunk limit u auto-pipeline-u
- `auto_pipeline_task` ne limitira broj chunkova koji se šalju u prompt
- Dokument sa 44k chunkova (VMware) generiše prompt od milion+ tokena
- Provideri timeout-uju ili vraćaju garbage
- Nema provere `token_count` ili chunk count pre generacije

### Problem 4: Nedostatak logging-a za konverzije tipova
- Kada se MC→CB konvertuje, nema log zapisa
- Nemoguće je dijagnostikovati zašto je došlo do konverzije
- Nema metrike koliko često se konverzija dešava

### Problem 5: Nema category-awareness za tip pitanja
- Prompt ne zna kojoj kategoriji pripada dokument
- Za "Hemija" (sa formulama) bi trebalo `chemical_equation`, za "IT" bi trebalo više `multiple_choice`
- Subject detection postoji ali se ne koristi za izbor tipa pitanja

### Zašto su povezani
Svi problemi se manifestuju u `generation.py` i `service.py` — prvi je kvalitet output-a, drugi je performansa/robusnost, treći je skalabilnost.

## Taskovi

### Phase 1: Prompt Improvement (Developer)

#### Task 1: Dodati semantička pravila u quiz prompt

| Aspect | Detail |
|--------|--------|
| **Šta** | Dodati instrukcije u QUIZ_PROMPT koje objašnjavaju KADA koristiti multiple_choice vs checkbox |
| **Acceptance** | Prompt sadrži: "If MULTIPLE options are factually correct → checkbox. If ONLY ONE → multiple_choice." |
| **Files** | `backend/app/services/quiz/prompts/quiz_prompt.py` |
| **Scope** | Small (1 file) |

#### Task 2: Dodati post-validation za multiple_choice sa svim tačnim opcijama

| Aspect | Detail |
|--------|--------|
| **Šta** | U `_validate_questions()` dodati heuristiku koja detektuje multiple_choice gde su sve opcije prisutne u tekstu i konvertuje u checkbox |
| **Acceptance** | Ako AI vrati multiple_choice sa 4+ opcije i >=3 su direktno iz teksta → konvertuje se u checkbox sa upozorenjem |
| **Files** | `backend/app/services/quiz/helpers/__init__.py` |
| **Scope** | Small (1 file) |

### Phase 2: Pipeline Timeout Fix (Developer)

#### Task 3: Dodati per-provider timeout u generation.py

| Aspect | Detail |
|--------|--------|
| **Šta** | Dodati `PER_PROVIDER_TIMEOUT = 45` (sekundi) u fallback petlju umesto 120s |
| **Files** | `backend/app/services/quiz/generation.py` |
| **Scope** | Small (1 file) |

#### Task 4: Dodati Celery soft_time_limit na taskove

| Aspect | Detail |
|--------|--------|
| **Šta** | Dodati `soft_time_limit=300` i `time_limit=360` na `generate_quiz_task` i `auto_pipeline_task` |
| **Files** | `backend/app/workers/tasks/quiz.py` |
| **Scope** | Small (1 file) |

#### Task 4a: Proveriti i popraviti timeout u openai.py i claude.py

| Aspect | Detail |
|--------|--------|
| **Šta** | Proveriti da li `openai.py` i `claude.py` imaju hardcoded timeout (kao `openai_compat.py`). Ako da, dodati parametrizaciju. |
| **Acceptance** | Svi provideri koriste konzistentan timeout mehanizam koji poštuje `PER_PROVIDER_TIMEOUT` |
| **Files** | `backend/app/services/quiz/clients/openai.py`, `backend/app/services/quiz/clients/claude.py` |
| **Scope** | Small (1-2 files) |

#### Task 4b: Dodati chunk limit u auto-pipeline

| Aspect | Detail |
|--------|--------|
| **Šta** | U `auto_pipeline_task` i `generate_quiz_task` dodati limit na broj chunkova (npr. max 50) i proveru `token_count`. Ako dokument ima previše chunkova, uzeti sample (najrelevantnije ili random). |
| **Acceptance** | Dokument od 44k chunkova ne generiše prompt od milion tokena. Samo prvih N chunkova se koristi. |
| **Files** | `backend/app/services/quiz/generation.py`, `backend/app/workers/tasks/quiz.py` |
| **Scope** | Medium (2 files) |

#### Task 4c: Univerzalna pravila umesto per-category instrukcija (ARCHITECTURE DECISION)

| Aspect | Detail |
|--------|--------|
| **Šta** | Umesto hardkodovanih instrukcija po kategoriji, koristimo **univerzalna semantička pravila** u `quiz_prompt.py`. `subjects.py` sadrži samo WHAT da se pita, ne WHICH tip. |
| **Acceptance** | Question type selection je univerzalan — zasnovan na analizi sadržaja dokumenta, ne na kategoriji. Subject instrukcije ne pominju tipove pitanja. |
| **Files** | `backend/app/services/quiz/prompts/quiz_prompt.py`, `backend/app/services/quiz/prompts/subjects.py` |
| **Scope** | Small (2 files) |
| **Razlog** | Vidi Architectural Decision iznad. Kategorije su preširoke, ne znamo unapred tip dokumenta, AI treba sam da proceni na osnovu sadržaja. |

#### Task 4d: Dodati logging za MC→CB konverziju

| Aspect | Detail |
|--------|--------|
| **Šta** | Logovati svaku MC→CB konverziju sa: originalnim opcijama, razlogom konverzije, document_id, providerom. Koristiti logger umesto print. |
| **Acceptance** | Svaka konverzija se loguje na `INFO` nivou. Može se pratiti koliko često se konverzija dešava. |
| **Files** | `backend/app/services/quiz/helpers/__init__.py` |
| **Scope** | Small (1 file) |

### Phase 3: Testovi (Tester)

#### Task 5: Napisati testove za novu prompt logiku

| Aspect | Detail |
|--------|--------|
| **Šta** | Testovi koji proveravaju da prompt sadrži semantička pravila za izbor tipa pitanja |
| **Files** | `backend/app/tests/unit/test_quiz_service.py` (novi testovi u `TestQuizPrompt`) |
| **Scope** | Small (1 file) |

#### Task 6: Napisati testove za validaciju multiple_choice→checkbox konverzije

| Aspect | Detail |
|--------|--------|
| **Šta** | Testovi za novu heuristiku u `_validate_questions()`: detekcija "svi tačni" opcija, konverzija u checkbox |
| **Files** | `backend/app/tests/unit/test_quiz_service.py` (novi testovi u `TestValidateQuestions`) |
| **Scope** | Small (1 file) |

#### Task 7: Napisati testove za timeout mehanizam

| Aspect | Detail |
|--------|--------|
| **Šta** | Testovi za per-provider timeout u fallback petlji |
| **Files** | `backend/app/tests/unit/test_generation.py` (novi fajl) |
| **Scope** | Small (1 file) |

### Phase 4: Code Review (Code Reviewer)

#### Task 8: Review svih izmena

| Aspect | Detail |
|--------|--------|
| **Šta** | Proći kroz svaki izmenjen fajl i proveriti: backward compatibility, edge cases, performance |
| **Verifikacija** | Flake8 clean, svi testovi prolaze, coverage ne pada |
| **Files** | All changed files |

### Phase 5: Dokumentacija i Evidencija

#### Task 9: Sačuvati test case evidence

| Aspect | Detail |
|--------|--------|
| **Šta** | Dokumentovati realan test slučaj (Podman mount pitanje) kao trajnu evidenciju: input → očekivani output → stvarni output. Dodati komentar u test fajlove koji referencira ovaj scenario. |
| **Files** | `backend/app/tests/unit/test_quiz_service.py` (komentar/dokumentacija u test klasi) |
| **Scope** | Small |

#### Task 10: Pokrenuti full suite i sačuvati rezultate

| Aspect | Detail |
|--------|--------|
| **Šta** | Pokrenuti kompletan test suite, sačuvati rezultat (broj testova, failova, skipova), coverage report, flake8 rezultat. |
| **Output** | Zapis u `docs/plans/REZULTATI_QUIZ_QUALITY.md` |
| **Scope** | Small |

#### Task 11: Finalna validacija i AGENTS.md update

| Aspect | Detail |
|--------|--------|
| **Šta** | Verifikovati: (1) backward compatibility — stari testovi prolaze, (2) novi behavior — novi testovi prolaze, (3) lint — flake8 clean. Zapisati u AGENTS.md: šta je urađeno, fajlovi, rezultati. |
| **Files** | `AGENTS.md` |
| **Scope** | Small |

## Dependency Graph

```
Task 1 (prompt rules + category awareness)
    │
    ├── Task 2 (post-validation + logging + MC->CB)  ──┐
    │                                                   │
    ├── Task 5 (prompt tests) ──────────────────────────┤
    │                                                   ├── Task 8 (code review)
    ├── Task 6 (validation tests) ──────────────────────┘
    │
    ├── Task 3 (per-provider timeout)
    │     │
    │     ├── Task 4 (Celery timeout)
    │     ├── Task 4a (openai.py/claude.py timeout)
    │     └── Task 7 (timeout tests)
    │
    ├── Task 4b (chunk limit)
    │
    └── Task 9 (evidence) ─── Task 10 (suite) ─── Task 11 (agents.md update)
```

## Checkpoint Plan

| Checkpoint | After | Verifikacija |
|------------|-------|-------------|
| **CP1: Prompt + Validation** | Tasks 1-2 + 4c + 4d | Prompt sadrži nova pravila + category awareness, validacija konvertuje MC→CB + logging, chunk limit postoji |
| **CP2: Pipeline fix** | Tasks 3-4-4a-4b | Celery taskovi imaju timeout, per-provider timeout radi, openai.py/claude.py imaju parametrizovan timeout, chunk limit štiti od ogromnih promptova |
| **CP3: Testovi** | Tasks 5-7 | Svi testovi prolaze (800+), coverage ne pada |
| **CP4: Review** | Task 8 | Flake8 clean, nema regresija |
| **CP5: Evidencija** | Tasks 9-11 | Test case evidence sačuvana, suite rezultati dokumentovani, AGENTS.md ažuriran |

## Edge Case Matrix

| Scenario | Očekivano ponašanje |
|----------|---------------------|
| AI vrati multiple_choice sa svim tačnim opcijama | Konvertuje se u checkbox |
| AI vrati validan multiple_choice (samo 1 tačan) | Ostaje multiple_choice |
| AI vrati checkbox sa 1 tačnim (postojeći behavior) | Konvertuje se u multiple_choice |
| Sve opcije su kratke (< 3 reči) | Ne konvertuje (verovatno su "A, B, C, D" stil) |
| Provider timeout-uje | Prelazi na sledeći provider posle 45s |
| Svi provideri timeout-uju | Koristi fallback pitanja |
| Celery task pređe 5 minuta | Worker prekida task (soft_time_limit) |
| Dokument sa 44k chunkova | Samo prvih 50 chunkova se koristi za quiz |
| openai.py i claude.py timeout | Koristi parametrizovan timeout (PER_PROVIDER_TIMEOUT) |
| MC→CB konverzija | Loguje se sa svim detaljima (opcije, match count, question index) |
| Dokument bez prepoznate kategorije | Univerzalna semantička pravila i dalje rade — AI analizira sam sadržaj |

---

## Rezultati (popunjava se nakon implementacije)

### Test Suite Rezultati

| Datum | Broj testova | Passed | Failed | Skipped | Coverage |
|-------|-------------|--------|--------|---------|----------|
| | | | | | |

### Izmenjeni fajlovi

| Fajl | Promena |
|------|---------|
| | |

### Evidence: Test slučaj (Podman mount question)

**Input:** multiple_choice, opcije = [bind, volume, image, tmpfs, devpts, proc], sve opcije su validni mount tipovi iz teksta

**Očekivano:** Konvertuje se u checkbox

**Stvarni rezultat:** (popuniti)

### AGENTS.md Update Status

- [ ] Zabeleženo u AGENTS.md
- [ ] Datum upisa:
