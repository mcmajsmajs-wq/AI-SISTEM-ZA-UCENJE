================================================================================
PLAN REALIZACIJE — 7 unapređenja sistema
================================================================================
Datum: 2026-06-06
Procenjen ukupan trud: ~29h
================================================================================

Kako koristiti ovaj plan:
1. Svaka faza ima: zadatak, skill-ove, agente, procenu
2. Izvršava se fazu po fazu (osim ako nije označeno kao nezavisno)
3. Posle svake faze: `docker exec` testovi + commit


================================================================================
FAZA 1: quiz.py podela (4h) — VISOK PRIORITET
================================================================================

Zadatak: Podeliti app/services/quiz/service.py (3000+ linija) na:
  - quiz/generation.py      — AI pozivi + prompt template-i
  - quiz/evaluation.py      — provera odgovora, score-ovanje
  - quiz/service.py         — samo orchestration (tanak)

Potrebni agenti:    @architect (dizajn nove strukture)
                    @developer (implementacija)
                    @tester (testovi posle svake faze)
                    @python-reviewer (code review)

Potrebni skill-ovi: incremental-implementation
                    test-driven-development
                    code-review-and-quality

Nezavisno od: FAZA 4, 5, 7
Blokira: dalji razvoj quiz feature-a


================================================================================
FAZA 2: Paralelni prevodi (3h) — VISOK PRIORITET
================================================================================

Zadatak: Umesto sekvencijalnih LLM poziva, batch-ovi od 5-10:
  - asyncio.gather za paralelne pozive
  - Rate limit kontroler (RPM po provider-u)
  - Fallback: ako batch padne, pojedinačni retry

Potrebni agenti:    @developer
                    @tester

Potrebni skill-ovi: incremental-implementation
                    performance-optimization

Nezavisno od: FAZA 3, 5, 6, 7


================================================================================
FAZA 3: WebSocket/SSE notifikacije (8h) — SREDNJI PRIORITET
================================================================================

Zadatak: Korisnik dobija notifikaciju kad task završi:
  - Backend: SSE endpoint ili Redis pub/sub → WebSocket
  - Frontend: sluša event, automatski osveži UI
  - Support: export, prevod, scraping, quiz generacija

Potrebni agenti:    @architect (dizajn event sistema)
                    @developer (backend + frontend)
                    @tester (testovi)

Potrebni skill-ovi: api-and-interface-design
                    frontend-ui-engineering
                    incremental-implementation

Zavisno od: FAZA 5 (frontend state)
Nezavisno od: FAZA 1, 2, 4, 6, 7


================================================================================
FAZA 4: Celery pattern standardizacija (2h) — SREDNJI PRIORITET
================================================================================

Zadatak: Svi taskovi → thin wrapperi:
  - translate_document_task → ✅ vec thin
  - process_pdf_task → extractovati logiku u servis
  - generate_quiz_task → extractovati logiku u servis
  - Dodati: standard error handling, retry politika, timeout

Potrebni agenti:    @developer
                    @tester
                    @refactor-cleaner

Potrebni skill-ovi: incremental-implementation
                    code-simplification

Nezavisno od: FAZA 2, 3, 5, 6, 7


================================================================================
FAZA 5: Frontend state audit + React Query (4h) — SREDNJI PRIORITET
================================================================================

Zadatak:
  1. Audit: koji state management se trenutno koristi?
  2. Ako nema: dodati React Query (TanStack Query)
  3. Migrirati postojeće API pozive na React Query hooks
  4. Automatski: caching, polling, retry, optimistic updates

Potrebni agenti:    @developer (frontend)
                    @tester

Potrebni skill-ovi: frontend-ui-engineering
                    incremental-implementation

Zavisno od: ničega
Blokira: FAZA 3 (WebSocket integracija sa frontendom)


================================================================================
FAZA 6: RAG hybrid search (6h) — NIZAK PRIORITET
================================================================================

Zadatak:
  - Dodati BM25 pretragu (whoosh ili PostgreSQL full-text search)
  - Ubaciti reranker (cross-encoder/ms-marco-MiniLM-L-6-v2)
  - Fusion: embedding × 0.7 + BM25 × 0.3 → reranker sortira
  - Opcioni: recency boost, source_type filter

Potrebni agenti:    @architect (dizajn)
                    @developer
                    @tester
                    @database-reviewer (BM25 optimizacija)

Potrebni skill-ovi: api-and-interface-design
                    test-driven-development

Nezavisno od: FAZA 1, 2, 4
Zavisno od: ničega


================================================================================
FAZA 7: Error reporting (2h) — NIZAK PRIORITET
================================================================================

Zadatak:
  - Integrisati Sentry (besplatni tier) ili webhook
  - Dodati middleware za neočekivane greške
  - Strukturirani JSON logovi za Celery taskove
  - Opciono: Slack notifikacija za N+ palih taskova

Potrebni agenti:    @developer
                    @tester

Potrebni skill-ovi: security-and-hardening
                    ci-cd-and-automation

Nezavisno od: FAZA 1, 2, 4, 5, 6


================================================================================
TIMING / REDOSLED
================================================================================

Preporučeni redosled izvršavanja (zavisnosti + prioritet):

1. FAZA 1 — quiz.py podela          [4h]  ⬅️ VISOK, blokira
2. FAZA 2 — paralelni prevodi       [3h]  ⬅️ VISOK, nezavisan
   ─────────────────────────────────────
3. FAZA 5 — frontend state          [4h]  ⬅️ SREDNJI, blokira F3
4. FAZA 3 — WebSocket/SSE           [8h]  ⬅️ SREDNJI, zavisi od F5
   ─────────────────────────────────────
5. FAZA 4 — Celery pattern          [2h]  ⬅️ SREDNJI, nezavisan
   ─────────────────────────────────────
6. FAZA 6 — RAG hybrid search       [6h]  ⬅️ NIZAK
7. FAZA 7 — error reporting         [2h]  ⬅️ NIZAK

Ukupno sekvencijalno: ~29h
Sa paralelizacijom (faze 1+2 u isto vreme): ~25h


================================================================================
MAPA AGENATA I SKILL-OVA
================================================================================

Agent           | Nadležnost                          | Ključni skill-ovi
----------------|-------------------------------------|--------------------------------
@architect      | Dizajn, arhitektura, odluke         | spec-driven-development
@developer      | Implementacija feature-a             | incremental-implementation, tdd
@tester         | Testiranje, coverage, kvalitet       | test-driven-development
@python-reviewer| Code review (Python bezbednost)     | code-review-and-quality
@database-reviewer| SQL, migracije, performanse      | ai-learning-db
@refactor-cleaner| Mrtav kod, čišćenje               | code-simplification
@build-error-resolver| TS greške, build fixes        | (nema poseban skill)

Skill             | Kada se koristi
------------------|----------------
incremental-implementation| Svaka promena >1 fajla
test-driven-development   | Pre pisanja koda
code-review-and-quality   | Pre commit-a
api-and-interface-design  | Novi endpoint-i
frontend-ui-engineering   | UI komponente
code-simplification       | Refactoring
spec-driven-development   | Nova funkcionalnost
performance-optimization  | Optimizacije
security-and-hardening    | Auth, input, data
ci-cd-and-automation      | Deployment, monitoring
