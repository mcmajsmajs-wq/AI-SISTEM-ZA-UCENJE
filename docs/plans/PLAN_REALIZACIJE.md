================================================================================
PLAN REALIZACIJE — Preostala unapređenja (ažurirano: 2026-07-02)
================================================================================
Prethodna verzija: 2026-06-06
Status: Ažuriran na osnovu audita koda (vidi NEDOSTAJUCE_STVARI.md za detalje)
================================================================================

NAPOMENA: Originalni plan je imao 7 faza (~29h). 
Nakon audita, FAZA 5 je GOTOVA, ostale su delimične ili netaknute.
Dodate su 3 nove faze (8, 9, 10) koje su realno preostale.

Procenjen ukupan trud: ~23h
================================================================================

Kako koristiti ovaj plan:
1. Svaka faza ima: zadatak, procenu, zavisnosti
2. Izvršava se fazu po fazu (osim ako nije označeno kao nezavisno)
3. Posle svake faze: testovi + commit


================================================================================
FAZA 1: Izdvajanje generation.py iz service.py (~2h) — VISOK PRIORITET
================================================================================

Originalni plan: "Podeliti service.py (3000+ linija)" 
Ažurirano: service.py je 685 linija, evaluation.py već izdvojen ✅

Preostalo:
  - Izdvojiti AI generaciju (generate_questions_with_ai, fallback chain)
    iz service.py u quiz/generation.py
  - service.py ostaje tanak orchestrator

Potrebni agenti:    @architect, @developer, @tester
Blokira: dalji razvoj quiz feature-a
Nezavisno od: FAZA 4, 7


================================================================================
FAZA 2: Paralelni prevodi (~3h) — VISOK PRIORITET
================================================================================

Zadatak: Umesto sekvencijalnih LLM poziva, batch-ovi od 5-10:
  - asyncio.gather za paralelne pozive
  - Rate limit kontroler (RPM po provider-u)
  - Fallback: ako batch padne, pojedinačni retry

Potrebni agenti:    @developer, @tester
Nezavisno od: FAZA 3, 8, 9


================================================================================
FAZA 3: WebSocket/SSE notifikacije (~8h) — SREDNJI PRIORITET
================================================================================

Zadatak: Korisnik dobija notifikaciju kad task završi:
  - Backend: SSE endpoint ili Redis pub/sub → WebSocket
  - Frontend: sluša event, automatski osveži UI
  - Support: export, prevod, scraping, quiz generacija

Napomena: SSE već postoji za chat streaming, ali NE za notifikacije.

Potrebni agenti:    @architect, @developer, @tester
Zavisno od: ničega


================================================================================
FAZA 4: Rate limiting aktivacija (~1h) — SREDNJI PRIORITET
================================================================================

NOVO — NIJE BILO U ORIGINALNOM PLANU.

Zadatak:
  - slowapi je već importovan u main.py, limiter kreiran
  - ALI nema @limiter.limit(...) dekoratora ni na jednom endpointu
  - Dodati limite na: /auth/register (5/min), /auth/login (10/min),
    /chat (30/min), /quiz (20/min), /translate (10/min)
  - Testirati da radi

Potrebni agenti:    @developer, @tester
Nezavisno od: FAZA 1, 2, 6


================================================================================
FAZA 5: Celery pattern standardizacija (~1h) — SREDNJI PRIORITET
================================================================================

Originalni plan: 2h — smanjeno jer je delimično urađeno.

Zadatak:
  - process_pdf_task: extractovati logiku u servis (trenutno inline)
  - Dodati soft_time_limit i time_limit na sve taskove
  - Standardizovati retry politiku (max_retries, countdown)

Potrebni agenti:    @developer, @tester, @refactor-cleaner
Nezavisno od: FAZA 2, 3, 8


================================================================================
FAZA 6: Error reporting (~2h) — NIZAK PRIORITET
================================================================================

Zadatak:
  - Integrisati Sentry (besplatni tier) ili webhook
  - Dodati middleware za neočekivane greške
  - Strukturirani JSON logovi za Celery taskove
  - Opciono: Slack notifikacija za N+ palih taskova

Potrebni agenti:    @developer, @tester
Nezavisno od: FAZA 1, 2, 4, 8


================================================================================
FAZA 7: RAG hybrid search (~4h) — NIZAK PRIORITET
================================================================================

Originalni plan: 6h — smanjeno jer pgvector infrastruktura već postoji.

Već postoji:
  ✅ pgvector ekstenzija (koristi se u CI)
  ✅ Embeddings generacija i storage u knowledge_chunks tabeli
  ✅ ::vector cast za upite

Nedostaje:
  - BM25 pretraga (Whoosh ili PostgreSQL FTS)
  - Reranker (cross-encoder)
  - Fusion: embedding × 0.7 + BM25 × 0.3
  - Search endpoint
  - Autocomplete, filteri, rangiranje

Potrebni agenti:    @architect, @developer, @tester, @database-reviewer
Nezavisno od: FAZA 1, 2, 4


================================================================================
FAZA 8: QA i sitne popravke (~2h) — SREDNJI PRIORITET
================================================================================

NOVO — NIJE BILO U ORIGINALNOM PLANU.

Zadaci:
  - Quiz quality pipeline: timeout-i po provideru (45s), MC→CB konverzija,
    chunk limit (max 50)
  - Human-in-the-loop review (ako je hitno): side-by-side prevod, inline edit


================================================================================
TIMING / REDOSLED
================================================================================

Preporučeni redosled (prioritet + zavisnosti):

1. FAZA 1 — generation.py izdvajanje       [2h]  ⬅️ VISOK
2. FAZA 2 — paralelni prevodi              [3h]  ⬅️ VISOK, nezavisan
   ─────────────────────────────────────
3. FAZA 4 — rate limiting aktivacija        [1h]  ⬅️ SREDNJI
4. FAZA 5 — Celery standardizacija          [1h]  ⬅️ SREDNJI, nezavisan
5. FAZA 3 — WebSocket/SSE notifikacije      [8h]  ⬅️ SREDNJI
   ─────────────────────────────────────
6. FAZA 8 — QA i sitne popravke            [2h]  ⬅️ SREDNJI
   ─────────────────────────────────────
7. FAZA 7 — RAG hybrid search              [4h]  ⬅️ NIZAK
8. FAZA 6 — error reporting                [2h]  ⬅️ NIZAK

Ukupno sekvencijalno: ~23h
Sa paralelizacijom (faze 1+2 u isto vreme): ~19h


================================================================================
ŠTO JE GOTOVO (iz originalnog plana)
================================================================================

FAZA 5 (Frontend state audit + React Query) — ✅ GOTOVO
  React Query (@tanstack/react-query ^5.24.0) već u upotrebi na 21 stranici.
  Zustand za client state, React Router v6 za routing.
