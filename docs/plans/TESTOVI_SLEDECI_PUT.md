# CrewAI integracija — Test status i plan za sledeći put

## Trenutni status testova (Jul 2026)

### Frontend: 54 testova ✅
| Fajl | Testova | Šta pokriva |
|------|---------|-------------|
| `src/test/api.test.ts` | 12 | API konfiguracija (base URL, auth, users endpoints), request/response tipovi, error handling (401, 404, 500), headers |
| `src/test/types.test.ts` | 12 | User, Token, LoginCredentials, RegisterData, UserStats interfejsi; email validacija, password strength, date formatting |
| `src/test/test_recent_fixes.test.ts` | 18 | FlashcardsPage data extraction, null safety za due cards, QuizResultsPage null safety, FlashcardReviewPage card null safety, DeckDetailPage error handling |
| `src/test/flashcards.test.ts` | 12 | Flashcard tipovi (Deck, Flashcard, ReviewRequest/Response, DueCardsResponse, GenerateFlashcardsResponse); API endpoint struktura (deck CRUD, card, review, generate) |

### Backend: 61 testova ✅ (od toga 9 CrewAI)
| Test klasa | Testova | Šta pokriva |
|-----------|---------|-------------|
| `TestSM2Algorithm` | 9 | SM-2 algoritam: first review quality 5, second review quality 4, third review, quality 0/1/2 reset, quality 3 minimum pass, EF clamping, delayed interval |
| `TestDeckCrud` | 8 | List/create/get/delete deck, not found, wrong user, multiple decks |
| `TestFlashcardCrud` | 2 | Add card (single + batch) |
| `TestReviewFlow` | 5 | Review card: first time, nonexistent, wrong user, low quality reset, full flow |
| `TestDueCards` | 1 | Due cards: empty when no cards |
| `TestGenerateFromDocument` | 3 | Generate from document: no chunks error, auto mode, AI mode |
| `TestChunkQualityFilter` | 12 | Metadata chunk filtering: empty, too short, Serbian CIP/title/editorial/TOC, English publisher/CIP/translator/copyright; content chunks pass (English + Serbian) |
| `TestAutoModeQuestionQuality` | 5 | Auto mode: complete fronts, comma splitting, English content, quoted terms extraction |
| `TestSplitSentences` | 5 | Sentence splitting: Serbian, English, ellipsis, single sentence, empty |
| `TestAIGenerationErrorHandling` | 2 | Error wrapping: no chunks error, API key error |
| **`TestCrewAIQuizQuestionFlow`** | **7** | **CrewAI quiz generation:** flow creation, valid question format, valid question types, num_questions limit, missing API key error, fallback in generation module (2 tests) |
| **`TestCrewAIIntegration`** | **3** | **CrewAI flashcard generation:** agent creation, fallback when provider fails, valid flashcard format |

### CrewAI testovi detaljno

| Test name | Šta proverava |
|-----------|---------------|
| `test_quiz_question_flow_can_be_created` | `QuizQuestionFlow` se može kreirati sa LLM-om, text-om i num_questions |
| `test_quiz_question_flow_returns_valid_question_format` | Flow vraća validan format pitanja (question_text, question_type, options, correct_answer, explanation) |
| `test_quiz_question_types_are_valid` | Tipovi pitanja (multiple_choice, true_false, fill_blank) prolaze kroz `_validate_questions` |
| `test_quiz_question_flow_respects_num_questions_limit` | Flow poštuje limit num_questions |
| `test_generate_quiz_questions_raises_without_api_key` | Error kada API ključ nije podešen |
| `test_crewai_quiz_fallback_in_generation_module` | Pad CrewAI quiz generacije → fallback na običan LLM |
| `test_crewai_quiz_fallback_without_api_key` | Nedostaje API ključ → fallback |
| `test_crewai_flow_agents_can_be_created` | CrewAI agenti (Reader, Generator, Validator) mogu se kreirati |
| `test_crewai_fallback_when_provider_fails` | Pad CrewAI flashcard generacije → fallback na stari `_generate_with_ai` |
| `test_crewai_flow_returns_valid_format` | FlashcardFlow vraća karte sa front/back/source_chunk_id |

## Plan za ručno testiranje (sledeći put)

### Pre testiranja
1. Log in na AI Learning (http://localhost:8090)
2. Proveri da imaš barem jedan obrađen dokument sa chunky

### Test scenario 1: Auto generisanje kartica
1. Otvori dokument → klikni "Generate Flashcards"
2. Izaberi **"Auto"** mod
3. Potvrdi
4. **Očekivano:** Deck se kreira, kartice su generisane, toast pokazuje uspeh
5. **Proveri:** kartice imaju front > 10 karaktera, back > 10 karaktera

### Test scenario 2: AI generisanje (single LLM)
1. Otvori dokument → klikni "Generate Flashcards"
2. Izaberi **"AI (OpenAI)"** mod
3. Potvrdi
4. **Očekivano:** Deck se kreira, `provider_used` = "openai"
5. **Proveri:** kvalitet kartica (potpuna pitanja, tačni odgovori)

### Test scenario 3: AI generisanje (CrewAI)
1. Otvori dokument → klikni "Generate Flashcards"
2. Izaberi **"AI (CrewAI)"** mod
3. Potvrdi
4. **Očekivano:** Deck se kreira, `provider_used` = "crewai"
5. **Proveri:** kvalitet kartica (treba da bude bolji nego single LLM)
6. **Proveri toast poruku:** treba da piše "CrewAI"

### Test scenario 4: CrewAI fallback
1. Obrisi API ključ (OpenAI -> "" -> Save)
2. Pokušaj da generišeš sa "AI (CrewAI)" modom
3. **Očekivano:** Toast pokazuje grešku ili fallback na single LLM
4. Vrati API ključ

### Test scenario 5: Quiz generacija sa CrewAI
1. Otvori dokument → idi na Quiz sekciju
2. Generiši kviz
3. **Očekivano:** Pitanja su generisana
4. **Proveri:** tipovi pitanja (multiple_choice, true_false, fill_blank)

### Test scenario 6: Review kartica
1. Idi na Flashcards stranu
2. Klikni na deck
3. Review kartice (klikni "Show Answer" → rate quality)
4. **Očekivano:** XP se dodeljuje, streak se ažurira, badges se dodeljuju
5. **Proveri:** sledeća kartica se pojavljuje
6. **Proveri:** summary na kraju

### Test scenario 7: Error handling
1. Ugasi container (`docker stop ai-learning-app`)
2. Pokušaj da generišeš kartice
3. **Očekivano:** Toast greška "Connection refused" ili slično
4. Upali container nazad

### Test scenario 8: Više provajdera
1. Podesi Groq API ključ (Settings → API Keys)
2. Generiši kartice sa Groq (AI mod)
3. Ponovi za Gemini i Mistral (ako imaš ključeve)
4. **Očekivano:** Svaki provajder generiše kartice

### Šta gledati u konzoli (F12 → Console)
- API pozivi na `/api/v1/documents/{id}/generate-flashcards`
- Response sadrži `provider_used` polje ("crewai", "openai", "groq", itd.)
- Error toast poruke na srpskom
- Nema `Cannot read properties of undefined (reading 'front')`

### Šta gledati u backend logovima
```bash
docker logs ai-learning-app --tail 50
```
- `CrewAI flashcard generation succeeded for provider openai`
- `CrewAI produkovao 0 validnih kartica.`
- `CrewAI validation: >50% invalid, retrying generation once`
- `Fallback to old _generate_with_ai because: ...`

## Test podaci

### Dokumenti za testiranje
1. **Engleski dokument (lakši test):** Bilo koji stručni tekst na engleskom (npr. članak o biologiji, istoriji)
2. **Srpski dokument:** Udžbenički tekst na srpskom (npr. istorija, geografija)
3. **Kratak dokument:** 1-2 pasusa za brzi test
4. **Dug dokument:** 10+ strana za test skalabilnosti

### Preporučeni test dokumenti
- `test_biology_article.txt` — Engleski, 2000 reči, biološki koncepti
- `test_history_serbian.txt` — Srpski, 1500 reči, istorijski događaji
- `test_short.txt` — Engleski, 200 reči, osnovni koncepti

## Poznati problemi
1. **Pydantic deprecation warnings** (`PydanticDeprecatedSince20: Support for class-based config is deprecated`) — treba migrirati na `ConfigDict`
2. **PytestMockWarning** u CrewAI testovima — mocker.patch ne treba da se koristi kao context manager, ali testovi prolaze
3. **FastAPI deprecation warnings** (`HTTP_422_UNPROCESSABLE_ENTITY` → `HTTP_422_UNPROCESSABLE_CONTENT`) — treba upgrade-ovati FastAPI
4. **OpenAI quota exceeded** — sam CrewAI flow radi, ali realni API pozivi padaju ako nema dovoljno kredita

## Komande za brzo testiranje

```bash
# Backend testovi (samo CrewAI)
docker exec ai-learning-app python3 -m pytest tests/test_flashcards.py -v -k "crewai"

# Backend testovi (svi flashcard testovi)
docker exec ai-learning-app python3 -m pytest tests/test_flashcards.py -v

# Frontend testovi
cd /home/dju/projects/ai-learning/frontend && npm run test -- --run

# Health check
curl http://localhost:8010/health

# Logovi
docker logs ai-learning-app --tail 20 -f

# Build
cd /home/dju/projects/ai-learning/frontend && npm run build
```
