================================================================================
ANALIZA SISTEMA — Primećeni problemi i predlozi za unapređenje
================================================================================
Datum: 2026-06-06
Autor: arhitektonska analiza celokupnog sistema (backend + frontend + infra)
================================================================================

SADRŽAJ:
  1. quiz.py — 3000+ linija (tehnički dug #1)
  2. Nema notifikacija za korisnika (WebSocket/SSE)
  3. RAG — samo embedding search, nema hybrid search + reranker
  4. Celery tasks — nekonzistentan pattern
  5. Frontend — nepoznat/nepostojeći state management
  6. Prevodi se rade sekvencijalno
  7. Nema centralnog error reporting-a


================================================================================
1. quiz.py — Preveliki fajl
================================================================================

Problem: 3000+ linija u jednom fajlu. Meša:
- DB logiku (SQLAlchemy upiti)
- AI pozive (prompt template-i, LLM komunikacija)
- Validaciju (provera odgovora, score-ovanje)
- Servisnu logiku (orchestration)

Posledice:
- Teško testirati (potrebno mock-ovati sve odjednom)
- Teško menjati (jedna promena rizikuje ceo fajl)
- Novi developeri se teško snalaze

Predlog: Podeliti na:
- quiz/generation.py — AI pozivi + prompt template-i
- quiz/evaluation.py — provera odgovora, score-ovanje
- quiz/service.py — samo orchestration (tanak sloj)

Prioritet: VISOK — blokira dalji razvoj quiz feature-a


================================================================================
2. Nema notifikacija za korisnika
================================================================================

Problem: Korisnik pokrene:
- Export u PDF (5-60s)
- Prevod dokumenta (minuti)
- Scraping web stranice (5-30s)
- Generaciju kviza (10-30s)

Dobije task_id, ALI nema način da sazna da je gotovo osim ručnog refresha.

Posledice:
- Frustrirajuće UX — korisnik ne zna da li radi ili je stalo
- Nepotrebni API pozivi (polling na svakih 5s)

Predlog: Dodati WebSocket ili SSE:
- Backend: emit event kad task završi (status_change)
- Frontend: sluša event, automatski osveži UI
- Alternativa: React Query polling (manje posla, malo više API poziva)

Prioritet: SREDNJI — UX problem, ne blokira funkcionalnost


================================================================================
3. RAG — samo embedding search
================================================================================

Problem: Trenutno:
- chunk_text() → embed → cosine similarity search
- Samo jedan način pretrage
- Nema težinskih faktora (recency, source quality)

Šta nedostaje:
- BM25 keyword search (paralelno sa embedding)
- Reranker (cross-encoder) koji sortira spojene rezultate
- Recency boost — noviji dokumenti imaju prednost
- Filteri po tipu dokumenta (upload vs web, datum)

Predlog:
- Dodati BM25 preko `whoosh` ili `sqlalchemy` full-text search
- Ubaciti reranker (besplatni `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- Spojiti rezultate: embedding × 0.7 + BM25 × 0.3 → reranker sortira

Prioritet: NIZAK — radi, ali može bolje. Trenutno dovoljno dobro za edukativni sajt.


================================================================================
4. Celery tasks — nekonzistentan pattern
================================================================================

Problem: Neki taskovi su:
- Thin wrapperi (dobar — samo poziva servis)
- Fat (300 linija sve u jednom)
- Neki imaju retry, neki nemaju
- Neki imaju timeout, neki default (večno čekanje)

Konkretno:
- translate_document_task → thin wrapper ✅
- generate_quiz_task → mešavina, pola logike u tasku
- process_pdf_task → fat, 200+ linija direktno

Predlog:
- Svi taskovi → thin wrapperi (samo pozivaju servis)
- Standardan error handling (try/except → status=error + stack trace)
- Retry politika: definisana po tasku (koji sme, koji ne)
- Timeout: maksimalno trajanje po tasku

Prioritet: SREDNJI — ne blokira, ali otežava debugging


================================================================================
5. Frontend — state management
================================================================================

Problem: Nepoznato stanje:
- Da li se koristi React Query? Zustand? Redux? Ili samo useState?
- Ako nema React Query → svaki API poziv zahteva ručno rukovanje loading/error state
- Ako nema caching → ista poruka se skida više puta

Predlog (ako nema):
- Dodati React Query (TanStack Query) — najlakši za integraciju
- Automatski: polling, caching, retry, optimistic updates
- Minimalna promena koda — hook-based

Prioritet: ZAVISI — treba prvo utvrditi trenutno stanje


================================================================================
6. Prevodi se rade sekvencijalno
================================================================================

Problem: 200 chunkova → 200 LLM poziva jedan po jedan.
- 200 × ~5s = 1000s (~17 minuta) za jedan dokument
- CPU/GPU većinu vremena miruje

Predlog:
- Batch-ovi od 5-10 paralelnih poziva (asyncio.gather ili Celery group)
- Rate limit: pratiti RPM (requests per minute) za svaki provider
  - Groq: max 30 RPM, batch 5 → 6 batch/min = 30 RPM ✅
  - Ollama (lokalni): batch 10, nema rate limita
- Fallback: ako batch padne, pojedinačni retry

Prioritet: VISOK — najveći uticaj na korisničko iskustvo (17min → 3min)


================================================================================
7. Nema centralnog error reporting-a
================================================================================

Problem: Kada Celery task padne:
- Upiše `document.status = "error"` u bazu
- Eventualno log u Docker logove
- Niko ne zna dok korisnik ne prijavi

Šta nedostaje:
- Slack/webhook notifikacija za ozbiljne greške
- Strukturirani logovi (JSON) za lakšu analizu
- Alert: "5+ taskova palo u poslednjih sat vremena"
- Sentry ili sličan monitoring

Predlog:
- Sentry (besplatni tier) — najlakši, hvata sve exception-e
- Ili: webhook + structured logging + periodic health check
- Dodati middleware koji hvata neočekivane greške i šalje notifikaciju

Prioritet: NIZAK — ne blokira, ali pomaže pri debugging-u


================================================================================
PRIORITIZACIJA
================================================================================

| # | Sta | Prioritet | Uticaj | Trud |
|---|-----|-----------|--------|------|
| 1 | Podeliti quiz.py | VISOK | Blokira razvoj | 4h |
| 2 | Paralelni prevodi | VISOK | UX (17min → 3min) | 3h |
| 3 | WebSocket/SSE | SREDNJI | UX | 8h |
| 4 | Celery pattern | SREDNJI | Debugging | 2h |
| 5 | Frontend state | SREDNJI | UX | 4h |
| 6 | RAG hybrid search | NIZAK | Kvalitet | 6h |
| 7 | Error reporting | NIZAK | Operative | 2h |

Ukupno: ~29h
