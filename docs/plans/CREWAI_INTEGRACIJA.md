# Plan: CrewAI integracija u AI Learning System

## 1. Cilj

Zameniti postojeci single-LLM poziv za generisanje flash kartica (`_generate_with_ai` u `flashcard.py`) sa CrewAI multi-agent Flow-om radi kvalitetnije obrade.

Trenutni problem: jedan LLM poziv mora istovremeno da ekstrahuje koncepte, kreira pitanja i validira — cesto daje iseckane ili nepotpune kartice.

## 2. Agent arhitektura

```
┌─────────────────────────────────────────────────────────┐
│                    CrewAI Flow                          │
│                                                         │
│  ┌──────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │ Content  │───▶│ Flashcard    │───▶│ Validator     │  │
│  │ Reader   │    │ Generator    │    │ Agent         │  │
│  └──────────┘    └──────────────┘    └───────┬───────┘  │
│       │                                      │          │
│       │                                      │          │
│       ▼                                      ▼          │
│  ┌──────────┐                           ┌───────────┐   │
│  │ Metadata │                           │ Format    │   │
│  │ Filter   │                           │ Output    │   │
│  └──────────┘                           └───────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Agent 1: Content Reader
- **Uloga**: Cita chunkove dokumenta, filtrira metadata
- **Ulaz**: sirovi chunkovi (vec filtrirani kroz `is_chunk_quality`)
- **Izvor**: prvih 10 chunkova (kao i sada)
- **Zadatak**: identifikuje glavne koncepte, teme, vazne termine
- **Output**: struktuirani sazetak sa listom koncepata

### Agent 2: Flashcard Generator
- **Uloga**: Na osnovu koncepata iz Reader-a kreira front/back parove
- **Ulaz**: struktuirani sazetak + originalni chunkovi
- **Zadatak**: za svaki koncept kreira pitanje (front) i odgovor (back)
- **Output**: JSON array `[{front, back}, ...]`
- **Kvalitet**: svaki front mora biti kompletan (ne iseckan), svaki back mora da odgovara

### Agent 3: Validator
- **Uloga**: Proverava kvalitet generisanih kartica
- **Ulaz**: generisane kartice + originalni tekst
- **Provere**:
  - Da li je front potpuna recenica (>10 karaktera)
  - Da li back sadrzi odgovor na pitanje iz front-a
  - Nema duplikata (semanticki slicni front-ovi)
  - Nema metadata sadrzaja u front-u
- **Output**: validirane kartice + lista odbacenih sa razlogom

### Agent 4: (opciono) Question Generator
- **Uloga**: Generise pitanja za kviz iz istog materijala
- **Ulaz**: struktuirani sazetak iz Content Reader-a
- **Output**: JSON array pitanja sa tipovima (multiple_choice, fill_blank, itd.)

## 3. Tok izvrsenja

```
1. n8n / Frontend → API → generate_from_document()
2. Filtriranje chunkova (is_chunk_quality - postoji)
3. Ako mode == "ai":
   a. CrewAI Flow start
   b. Content Reader procesuira chunkove
   c. Flashcard Generator kreira kartice
   d. Validator proverava kvalitet
   e. Ako validator odbaci >50% kartica → ponoviti (max 2 puta)
   f. Formatiranje output-a
4. Kreiranje deka i cuvanje u bazu
5. Povratak response-a sa provider_used = "crewai"
```

## 4. Faze implementacije

### Faza 1: Osnovni CrewAI agenti (1-2 dana)
- [ ] Instalacija crewai (zavrseno)
- [ ] Definisati CrewaiAgents klasu u `app/services/crewai_flashcard.py`
- [ ] Implementirati Content Reader agenta
- [ ] Implementirati Flashcard Generator agenta
- [ ] Implementirati Validator agenta
- [ ] Testirati sa test dokumentom

### Faza 2: Integracija sa postojecim sistemom (1 dan)
- [ ] Zameniti `_generate_with_ai` poziv sa CrewAI Flow-om
- [ ] Dodati `provider_used = "crewai"` u response
- [ ] Zadrzati fallback na single-LLM ako CrewAI nije dostupan
- [ ] Testirati generisanje iz UI-ja

### Faza 3: Prosirenje i optimizacija (1 dan)
- [ ] Dodati Question Generator agenta za kvizove
- [ ] Dodati caching (ako se isti dokument ponovo generise)
- [ ] Merenje vremena izvrsenja
- [ ] Dodati telemetriju (koji agent koliko traje)

## 5. Očekivani rezultati

| Metrika | Trenutno | Sa CrewAI |
|---------|----------|-----------|
| Kvalitet pitanja | Srednji (iseckani front-ovi) | Visok (validator proverava) |
| Metadata u pitanjima | Povremeno (ako filtriranje propusti) | Nikad (reader filtrira + validator) |
| Vreme generisanja | ~3-8s | ~8-15s |
| Duplikati | Mogući | Validator uklanja |
| Broj LLM poziva | 1 | 3 (reader + generator + validator) |

## 6. Rollout plan

1. Prvo u **auto modu** (samo za testiranje) — pored postojeceg `_generate_with_ai`
2. Zatim kao opcija "AI (CrewAI)" pored postojeceg "AI"
3. Ako je kvalitet stabilan, zameniti default "AI" mod

## 7. Fajlovi koje treba kreirati / izmeniti

- `backend/app/services/crewai_flashcard.py` — NOV: CrewAI agenti i Flow
- `backend/app/services/flashcard.py` — IZMENA: zameniti _generate_with_ai poziv
- `backend/app/schemas/flashcard.py` — IZMENA: dodati "crewai" kao provider
- `backend/requirements.txt` — IZMENA: dodati crewai (zavrseno)
- `frontend/src/pages/DeckDetailPage.tsx` — IZMENA: prikazati "CrewAI" u toast-u
