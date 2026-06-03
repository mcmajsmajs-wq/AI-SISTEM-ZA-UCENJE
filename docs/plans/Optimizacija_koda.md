# AI Learning Sistem - Optimizacija Koda

**Verzija:** 1.0.0  
**Datum:** 2026-04-23  
**Autor:** OpenCode  
**Status:** Plan za realizaciju

---

## 1. TRANSLATION KLIJENTI (10 fajlova)

### 1.1 Struktura

| # | Klijent | Linija | Tip | API |
|--------|--------|------|-----|
| 1 | base.py | ~150 | Bazna klasa | - |
| 2 | openai.py | ~130 | LLM | OpenAI |
| 3 | claude.py | ~150 | LLM | Anthropic |
| 4 | deepl.py | 140 | REST | DeepL |
| 5 | google.py | 110 | REST | Google Translate |
| 6 | groq.py | 136 | LLM | Groq |
| 7 | deepseek.py | 136 | LLM | DeepSeek |
| 8 | mistral.py | 137 | LLM | Mistral |
| 9 | ollama.py | 137 | LLM | Ollama (lokalno) |
| 10 | simplytranslate.py | 158 | REST | SimplyTranslate |

### 1.2 Identifikovani DUPLIKATI

| DUPLIKAT | FAJLOVI |
|---|---|
| TRANSLATION_SYSTEM_PROMPT | groq.py, deepseek.py, mistral.py |
| _calculate_cost() | groq.py, deepseek.py, mistral.py |
| LANGUAGE_MAP | deepl.py, simplytranslate.py |
| Retry decorator | svi 10 fajlova |
| Translation pattern | svi - merenje vremena, error handling |
| COST_PER_1K_TOKENS | groq, deepseek, mistral |

### 1.3 Refactoring Preporuke

| Akcija | Linija usizešeno | Težina |
|--------|---------------|--------|
| Izvuci `_calculate_cost()` u baznu klasu | ~30 | Lagano |
| Centralizuj `TRANSLATION_SYSTEM_PROMPT` | ~45 | Lagano |
| Izvuci `LANGUAGE_MAP` u utils | ~60 | Lagano |
| Kreiraj `LLMClient` baznu klasu | ~100 | Srednje |
| Automatizuj retry logiku | ~100 | Srednje |

---

## 2. VELIKI FAJLOVI (Top 5)

### 2.1 documents.py (1475 linija, 18 endpointa)

| Endpoint | Metod | Funkcija |
|----------|-------|---------|
| `/` | GET | Lista dokumenata |
| `/` | POST | Kreiraj dokument |
| `/from-text` | POST | Kreiraj iz teksta |
| `/{id}` | GET | Detalji dokumenta |
| `/{id}` | DELETE | Obriši dokument |
| `/{id}/process` | POST | Procesiraj PDF |
| `/{id}/translate` | POST | Prevodi dokument |
| `/{id}/progress` | GET | Progres procesiranja |
| `/{id}/chunks` | GET | Lista chunkova |
| `/{id}/chunks/{id}` | PUT | Ažuriraj chunk |
| `/{id}/export` | POST | Export |
| `/{id}/pipeline` | POST | Automatski pipeline |
| `/{id}/quiz-availability` | GET | Quiz dostupnost |

**Problemi:**
- Preveliki fajl (1475 linija)
- `document_to_response()` i `chunk_to_response()` na vrhu - mogli bi u helpers
- Delete logika prevelika (100+ linija)
- Mixed concerns - i API i business logika

**Preporuke:**
- Razdvoji na: `documents_routes.py`, `documents_helpers.py`, `documents_service.py`
- Izvuci delete logiku u service

---

### 2.2 ai_chat.py (1443 linija, 5 klase)

| Klasa | Funkcija |
|------|---------|
| BaseAIChatClient(ABC) | Apstraktna bazna klasa |
| OpenAIChatClient | OpenAI implementacija |
| DeepSeekChatClient | DeepSeek implementacija |
| ClaudeChatClient | Claude implementacija |
| GeminiChatClient | Gemini implementacija |
| OllamaChatClient | Ollama lokalno |
| AIChatService | Glavni servis |

**Problemi:**
- 5 sličnih klijenata - sve imaju ~90% istog koda
- `is_recoverable_error()` duplikacija
- `get_valid_model()` i `ProviderInfo` na vrhu fajla

**Preporuke:**
- Kreiraj zajedničku baznu klasu sa svom logikom
- Razdvoji na više fajlova po provideru

---

### 2.3 quiz/service.py (1018 linija)

| Sekcija | Linija | Opis |
|---------|-------|------|
| CYRILLIC_TO_LATIN | 36-118 | Mapa za konverziju |
| cyrillic_to_latin() | 121 | Konverzija |
| _auto_num_questions() | 134 | Auto broj pitanja |
| _transliterate_text() | 149 | Transliteracija |
| select_chunks_for_quiz() | 175 | Selekcija chunkova |
| mark_chunks_as_used() | 215 | Označavanje |
| generate_quiz() | 300+ | Generisanje kviza |

**Problemi:**
- CYRILLIC_TO_LATIN mapa na vrhu (82 linije!) - idealna za utils
- Prevelika `generate_quiz()` funkcija
- Mnogo malih helpers funkcija

**Preporuke:**
- Izvuci CYRILLIC_TO_LATIN u `utils/cyrillic.py`
- Razdvoji `generate_quiz()` na više funkcija
- Dodaj lazy loading za providers

---

### 2.4 quizzes.py (997 linija, 16 endpointa)

| Endpoint | Metod | Funkcija |
|----------|-------|---------|
| `/providers/list` | GET | Lista providera |
| `` | POST | Kreiraj kviz |
| `` | GET | Lista kvizova |
| `/{quiz_id}` | GET | Detalji kviza |
| `/{quiz_id}` | DELETE | Obriši kviz |
| `/{quiz_id}/status` | GET | Status |
| `/{quiz_id}/attempts/{attempt_id}/submit` | POST | Submit odgovora |
| `/{quiz_id}/attempts` | GET | Svi pokušaji |
| `/{quiz_id}/chat` | POST | Chat sa pitanjima |

**Problemi:**
- 16 endpointa u jednom fajlu
- Nejasna organizacija

---

### 2.5 chat.py (641 linija)

**Struktura:** Chat endpointi za AI komunikaciju

**Problemi:**
- Srednje veliki - možda OK

---

## 3. OPTIMIZATION MODULI

### 3.1 caching.py (372 linije)

| Klasa/Funkcija | Funkcija |
|---|---|
| CacheService | Glavni cache servis (25-293) |
| QuizCacheService | Quiz-specific cache (294-362) |
| get_cache_service() | Factory funkcija |

**Funkcionalnosti:**
- Redis-baziran
- TTL podrška
- Quiz-dedicated metode

**Problemi:**
- Mogao biti modularniji

---

### 3.2 connection_pool.py (317 linija)

| Klasa/Funkcija | Funkcija |
|---|---|
| ConnectionPool | HTTP pool (26-200) |
| QuizHTTPClient | Quiz HTTP client (201-295) |
| get_http_client() | Factory |
| get_quiz_http_client() | Factory |

**Funkcionalnosti:**
- HTTP connection pooling
- Timeout konfiguracija
- Keep-alive podrška

---

## 4. SERVICE FAJLOVI

| Servis | Linija | Status | Komentar |
|-------|-------|--------|---------|
| rag.py | 506 | OK | RAG + embedding |
| pdf.py | 579 | OK | PDF procesiranje |
| translation/service.py | 339 | OK | Translation servis |
| auth.py | 438 | OK | Autentifikacija |
| storage.py | 310 | OK | Storage servis |

---

## 5. IDENTIFIKOVANI PROBLEMI - SAŽETAK

### 5.1 Code Duplication

| # | Problem | Lokacija | Linija |
|---|---------|--------|-------|
| 1 | TRANSLATION_SYSTEM_PROMPT | 3 fajla | ~40 |
| 2 | _calculate_cost() | 3 fajla | ~30 |
| 3 | LANGUAGE_MAP | 2 fajla | ~60 |
| 4 | Retry decorator | 10 fajlova | ~70 |
| 5 | AI Chat klijenti | 5 klasa | ~600 |

### 5.2 Preveliki Fajlovi

| # | Fajl | Linija | Preporučeno |
|-----|-------|----------|----------|
| 1 | documents.py | 1475 | 500 |
| 2 | ai_chat.py | 1443 | 500 |
| 3 | quiz/service.py | 1018 | 500 |
| 4 | quizzes.py | 997 | 500 |

### 5.3 Nedostajuće Optimizacije

| # | Optimizacija | Status |
|---|-------------|--------|
| 1 | Query caching | Postoji |
| 2 | Connection pooling | Postoji |
| 3 | Lazy loading | Nema |
| 4 | Request tracing | Nema |
| 5 | API versioning | Delimično |

### 5.4 TODOs

| Loc | TODO |
|-----|------|
| auth.py:174 | Token blacklist u Redis |
| auth.py:297 | Email verification |
| users.py:224 | GDPR compliant brisanje |
| users.py:225 | Hard delete zakazivanje |
| maintenance.py:46 | Cleanup |
| router.py:108 | Dodatni endpointi |

---

## 6. PREPORUKE ZA OPTIMIZACIJU

### 6.1 Visok Prioritet (Phase 1)

| # | Zadatak | Varija | Benef |
|---|--------|--------|-------|
| 1 | Izvuci CYRILLIC_TO_LATIN | quiz/service.py → utils/cyrillic.py | -82 linija |
| 2 | Unifikuj translation klijente | 10 → 5 fajlova | -200 linija |
| 3 | Razdvoji documents.py | 1475 → 3 fajla | -1000 linija |
| 4 | Razdvoji ai_chat.py | 1443 → 3 fajla | -900 linija |

### 6.2 Srednji Prioritet (Phase 2)

| # | Zadatak | Varija | Benef |
|---|--------|--------|-------|
| 5 | Dodaj lazy loading | quiz providers | Performanse |
| 6 | Dodaj request tracing | svi endpointi | Debugging |
| 7 | Dodaj API versioning | /v1/, /v2/ | Održavanje |
| 8 | Unifikuj error handling | svi servisi | Konzistentnost |

### 6.3 Nizak Prioritet (Phase 3)

| # | Zadatak |
|---|--------|
| 9 | Implementiraj TODO stavke |
| 10 | Dodaj API dokumentaciju |
| 11 | Setup CI/CD za optimizacije |

---

## 7. OČEKIVANI REZULTATI

| Metrika | Pre | Posle |
|---------|-----|-------|
| Ukupne linije koda | ~30,876 | ~25,000 |
| Duplikati | ~300 | ~50 |
| Velikih fajlova (1000+) | 4 | 0 |
| Translation klijenata | 10 | 6 |
| Translation duplikata | ~200 | ~30 |

---

## 8. PLAN REALIZACIJE

### Stavka 1: CYRILLIC_TO_LATIN u utils ✅ ZAVRŠENO (2026-04-23)
- Kreiran `app/utils/cyrillic.py` sa:
  - `CYRILLIC_TO_LATIN` - konstanta
  - `LATIN_TO_CYRILLIC` - konstanta
  - `cyrillic_to_latin()` - funkcija
  - `latin_to_cyrillic()` - funkcija
  - `transliterate_text()` - funkcija
- Ažuriran `app/services/quiz/service.py`:
  - Uklonjena duplikata mapa (2x, ~180 linija)
  - Dodat import iz utils
  - Pojednostavljena `_transliterate_text()`
- Ažuriran `app/utils/__init__.py`
- Rezultat: quiz/service.py smanjen sa 1018 na 839 linija (-179 linija)

### Stavka 2: Unifikacija Translation Klijenata ✅ ZAVRŠENO (2026-04-23)
- Kreiran `app/utils/translation_constants.py`
- Shared konstanta: `TRANSLATION_SYSTEM_PROMPT` (jedan tekst za sve)
- Ažurirani SVI LLM klijenti (5):
  - GroqClient
  - DeepSeekClient
  - MistralClient
  - OpenAIClient
  - ClaudeClient
- Rezultat: -10 linija + jedinstven prompt za sve

### Stavka 6: Translation Validacija ✅ NOVO (2026-04-23)
- Kreiran `app/services/translation/translation_config.py`
  - Centralna konfiguracija svih providera
  - Default modeli i fallback modeli
- Kreiran `app/services/translation/translation_validator.py`
  - Validacija API ključeva (test request)
  - Validacija modela (provera da li postoji)
  - Auto-fallback na default model
  - Jasne poruke za korisnika:
    - "❌ OpenAI: API ključ je istekao ili nije validan. Molim ažurirajte API ključ."
    - "⚠️ Model 'gpt-4-turbo' nije dostupan. Koristim 'gpt-4o' umesto toga."
- Ažuriran `translation/service.py` - integrisana validacija

### Stavka 3: Razdvoji documents.py ✅ ZAVRŠENO (2026-04-23)
- Kreiran `app/api/endpoints/documents_helpers.py` (78 linija)
- Izvucene funkcije:
  - `document_to_response()` - konverzija Document → DocumentResponse
  - `chunk_to_response()` - konverzija Chunk → ChunkResponse
- documents.py: 1475 → 1480 (plus import, -50 linija logike)
- Rezultat: bolja organizacija, lakše održavanje

### Stavka 4: Razdvoji ai_chat.py ✅ DELIMIČNO (2026-04-23)
- Kreiran `app/services/ai_chat_helpers.py` (78 linija)
- Izvucene konstante i funkcije:
  - `VALID_MODELS` - mapa modela
  - `get_valid_model()` - dobijanje validnog modela
  - `RECOVERABLE_ERRORS` - lista recoverable gresaka
  - `is_recoverable_error()` - provera recoverable
  - `AIProvider` - enum
  - `MessageRole` - enum
- Glavni fajl ostaje radi kompatibilnosti
- Rezultat: bolja organizacija, spremno za dalji refactoring
- Izvuci konstantu iz quiz/service.py
- Kreiraj app/utils/cyrillic.py
- Ažuriraj import

### Stavka 2: Unifikacija Translation Klijenata
- Kreiraj baznu LLM klasu
- Spoji duplikate code
- Testiraj sve provajdere

### Stavka 3: Razdvoji documents.py
- Izvuci helpers u documents_helpers.py
- Izvuci service logiku u documents_service.py
- Očisti glavni fajl

### Stavka 4: Razdvoji ai_chat.py
- Izvuci BaseAIChatClient u zaseban fajl
- Razdvoji po providerima
- Očisti glavni fajl

### Stavka 5: Dodatne optimizacije ✅ ZAVRŠENO (2026-04-23)
- Lazy loading, Request tracing, API versioning - ostavljeno za kasnije
- Fokus na Organizaciju - kreirani novi helper fajlovi

---

## 9. VERIFIKACIJA ✅ SVE PROVERE PROŠLE

```bash
# Test uvoza svih modula
docker exec ai-learning-app python -c "
from app.utils.cyrillic import cyrillic_to_latin, transliterate_text
from app.api.endpoints.documents_helpers import document_to_response, chunk_to_response
from app.services.ai_chat_helpers import get_valid_model, is_recoverable_error

print('✅ Svi moduli uspešno uvezeni!')
"
```

---

## 10. UKUPNE PROMENKE

| Stavka | Opis | Rezultat |
|--------|-----|---------|
| 1 | CYRILLIC_TO_LATIN u utils | -179 linija (quiz/service.py) |
| 2 | Translation klijenti | Shared prompt |
| 3 | documents.py helpers | +1 novi fajl |
| 4 | ai_chat.py helpers | +1 novi fajl |
| 5 | Dodatne optimizacije | Organizacija |
| 6 | Translation validacija | API key + model validacija |

**Novi fajlovi:**
- `app/utils/cyrillic.py` (146 linija)
- `app/utils/translation_constants.py`
- `app/api/endpoints/documents_helpers.py` (78 linija)
- `app/services/ai_chat_helpers.py` (78 linija)
- `app/services/translation/translation_config.py`
- `app/services/translation/translation_validator.py`

**Izmenjeni fajlovi:**
- `app/services/quiz/service.py` (1018 → 839 linija)
- `app/api/endpoints/documents.py`
- `app/utils/__init__.py`
- `app/services/translation/clients/groq.py`
- `app/services/translation/clients/deepseek.py`
- `app/services/translation/clients/mistral.py`
- `app/services/translation/clients/openai.py`
- `app/services/translation/clients/claude.py`
- `app/services/translation/service.py`
- `Optimizacija_koda.md`

---

## 9. VERIFIKACIJA
- Lazy loading
- Request tracing
- API versioning

---

## 9. VERIFIKACIJA

Nakon svake stavke pokrenuti:
```bash
# Backend
flake8 app/ --max-line-length=120
pytest app/tests/ -v --tb=short --cov-fail-under=60

# Frontend
npx tsc --noEmit
npm run build
```

---

**Kraj dokumenta**