# INTEGRACIJA AI LEARNING SISTEMA SA MCP

## SADRŽAJ
1. UVOD I VIZIJA
2. ANALIZA POSTOJEĆEG SISTEMA
3. PREDNOSTI I MANE INTEGRACIJE
4. SKALIRANJE I PERFORMANSE (1000+ korisnika)
5. MULTI-TENANT IZOLACIJA
6. FAZA 1: Proširenje AI Providera
7. FAZA 2: Skill Sistem (Prompt Šabloni)
8. FAZA 3: Quiz i Translation u Bazi
9. FAZA 4: MCP Serveri
10. FAZA 5: User API Key Security
11. FAZA 6: Implementation Steps
12. TEHNIČKA DOKUMENTACIJA
13. PRILOZI

---

# 1. UVOD I VIZIJA

## 1.1 Cilj integracije

Omogućiti AI Learning sistemu da koristi MCP (Model Context Protocol) kao glavni interfejs za komunikaciju sa AI modelima, uz podršku za korisničke API ključeve (user-provided keys) za napredne korisnike.

## 1.2 Ključni zahtevi

- **User-provided API keys**: Svaki korisnik može uneti svoje API ključeve za različite provajdere
- **Skill sistem**: Automatska detekcija tipa PDF dokumenta i primena odgovarajućeg prompt template-a
- **Quiz sa translation**: Pitanja moraju biti sačuvana u bazi sa originalnim i prevedenim tekstom
- **Modularna arhitektura**: Više MCP servera po domenu (Quiz MCP, Translate MCP, Document MCP)
- **Skalabilnost**: Podrška za 1000+ simultanih korisnika
- **Multi-tenant izolacija**: Svaki korisnik vidi samo svoje podatke

---

# 2. ANALIZA POSTOJEĆEG SISTEMA

## 2.1 Trenutna arhitektura

```
┌─────────────────────────────────────────────────────────────┐
│                    EXISTING BACKEND                         │
├─────────────────────────────────────────────────────────────┤
│  Quiz Service (quiz.py)                                    │
│  - create_quiz, update_quiz, delete_quiz                   │
│  - add_question, update_question, delete_question       │
│  - start_attempt, submit_answer, complete_attempt         │
│  - generate_questions_from_chunks                          │
├─────────────────────────────────────────────────────────────┤
│  Translation Service (translation.py)                      │
│  - OllamaClient, DeepLClient, OpenAIClient                 │
│  - GoogleTranslateClient, ClaudeClient                     │
│  - translate(), translate_batch()                          │
├─────────────────────────────────────────────────────────────┤
│  Celery Tasks (tasks.py)                                   │
│  - process_pdf_task                                         │
│  - translate_document_task                                 │
│  - generate_quiz_task                                       │
└─────────────────────────────────────────────────────────────┘
```

## 2.2 Postojeći Provideri

| Provider | Endpoint | Status |
|----------|----------|--------|
| Ollama | http://localhost:11434 | ✅ Postoji |
| DeepL | https://api-free.deepl.com/v2 | ✅ Postoji |
| OpenAI | https://api.openai.com/v1/chat/completions | ✅ Postoji |
| Google Translate | https://translation.googleapis.com/v2 | ✅ Postoji |
| Claude | https://api.anthropic.com/v1/messages | ✅ Postoji |

## 2.3 Database Models

### Quiz Models (quiz.py)
- **Quiz**: id, document_id, user_id, title, description, total_questions, time_limit, passing_score, difficulty, status
- **Question**: id, quiz_id, question_text, question_type, options, correct_answer, explanation, points, difficulty
- **QuizAttempt**: id, quiz_id, user_id, score, percentage, passed, status
- **Answer**: id, attempt_id, question_id, selected_answer, is_correct, points_earned

---

# 3. PREDNOSTI I MANE INTEGRACIJE

## 3.1 Prednosti

| Prednost | Objašnjenje |
|----------|-------------|
| **Modularna arhitektura** | Svaki MCP server je nezavisni modul. Lako dodaješ nove funkcionalnosti bez diranja core logike. |
| **AI auto-discovery** | LLM automatski otkriva dostupne tool-ove bez ručnog programiranja. |
| **Standardizovan interfejs** | MCP protocol je standard - integracija sa raznim LLM klijentima je trivijalna. |
| **User-provided keys** | Nema potrebe za centralnim billing-om. Svaki korisnik plaća svoje API pozive direktno. |
| **Separacija odgovornosti** | Quiz logika, translate logika, skill logika - svaka u svom MCP serveru. |
| **Skill sistem** | Prompt šabloni postaju prvi-class citizens - LLM zna kako da koristi PDF. |
| **Latentno proširenje** | LLM može sam otkriti i koristiti tool-ove bez eksplicitnog poziva u kodu. |

## 3.2 Mane i Izazovi

| Izazov | Težina | Rešenje |
|--------|--------|---------|
| **User API key security** | 🔴 Visoka | Enkripcija na rest-u (AES-256), key validation, no key logging |
| **Multi-tenant izolacija** | 🔴 Visoka | Per-user session/context, user_id u svakom request-u |
| **Provider varijacije** | 🟡 Srednja | Unified interface za sve provajdere |
| **State management** | 🟡 Srednja | Stateless HTTP, user context u svakom request-u |
| **Performance overhead** | 🟢 Niska | Connection pooling, batch operacije |
| **Skaliranje na 1000+ korisnika** | 🔴 Visoka | Async/await, Celery workers, rate limiting |
| **AI Rate Limits** | 🔴 Visoka | Request queue, backoff, user quotas |

---

# 4. SKALIRANJE I PERFORMANSE (1000+ korisnika)

## 4.1 Arhitektura za skaliranje

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         LOAD BALANCER (nginx)                            │
│                    (Distribucija zahteva)                                │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         MCP GATEWAY SERVER                               │
│                  (Streamable HTTP, async/await)                         │
│                          Port: 8080                                      │
└──────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  QUIZ MCP       │  │ TRANSLATE MCP   │  │  DOCUMENT MCP   │
│  SERVER         │  │   SERVER        │  │   SERVER        │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     CELERY WORKERS (Redis Queue)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Worker 1    │  │ Worker 2    │  │ Worker 3    │  │ Worker N    │    │
│  │ Quiz Gen    │  │ Translate   │  │ PDF Process│  │ AI Requests │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└──────────────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  PostgreSQL     │  │     Redis       │  │     MinIO       │
│  (chunks, quiz)│  │  (cache, queue) │  │  (file storage) │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 4.2 Memorijska optimizacija

### 4.2.1 PDF tekst u bazi, ne u RAM-u

| Komponenta | Lokacija | Razlog |
|------------|----------|--------|
| PDF tekst | PostgreSQL (`chunks` tabela) | Chunk-ovi mogu biti veliki, PostgreSQL je optimizovan |
| PDF fajlovi | MinIO/S3 | Originalni fajlovi |
| Session podaci | Redis | Brzi pristup, TTL |
| User credentials | PostgreSQL (enkriptovano) | Trajno čuvanje |

### 4.2.2 Redis za cache i queue

```python
# Redis koristi za:
# 1. Celery broker (queue za zadatke)
# 2. Session cache (brzi pristup)
# 3. Rate limiting (token bucket)
# 4. Preview cache (PDF pages)

REDIS_KEYS = {
    "session": "session:{user_id}",
    "rate_limit": "rate:{user_id}:{provider}",
    "pdf_cache": "pdf:{document_id}:page:{page_num}",
    "quiz_preview": "quiz:{quiz_id}:preview",
}
```

## 4.3 Konkurentnost sa FastAPI

### 4.3.1 Async/await model

```python
# FastAPI je asinhron - može obrađivati hiljade simultanih zahteva
# dokle god boda i AI model mogu da prate tempo

@app.post("/mcp/v1/tools/quiz_create")
async def quiz_create(request: QuizCreateRequest, user_id: str = Header(X-User-ID)):
    # Ovo je async - ne blokira druge zahteve
    result = await mcp_server.call_tool("quiz_create", {...})
    return result
```

### 4.3.2 Worker pool sizing

| Broj korisnika | Preporučeni workeri | Redis konekcije |
|----------------|---------------------|-----------------|
| 100 | 2-4 | 10-20 |
| 500 | 4-8 | 20-50 |
| 1000+ | 8-16 | 50-100 |

## 4.4 AI Rate Limits

### 4.4.1 Provider ograničenja

| Provider | Request limit | Strategija |
|----------|---------------|------------|
| OpenAI (GPT-4) | ~500 req/min | Request queue + backoff |
| OpenAI (GPT-3.5) | ~3000 req/min | Više request-a dozvoljeno |
| Claude | Varira po planu | Request pooling |
| DeepSeek | 60 req/min | Rate limiting po useru |
| Mistral | Varira po planu | Queue sistem |
| Grok | 60 req/min | Rate limiting |
| Gemini | Varira po planu | Queue + batch |

### 4.4.2 Rate limiting implementacija

```python
class RateLimiter:
    """Rate limiter po korisniku i provideru."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    async def check_limit(self, user_id: str, provider: str, limit: int = 60) -> bool:
        """Proverava da li korisnik ima pravo na request."""
        key = f"rate:{user_id}:{provider}"
        
        current = await self.redis.get(key)
        if current and int(current) >= limit:
            return False
        
        # Inkrementiraj counter
        pipe = self.redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)  # 60 sekundi
        await pipe.execute()
        
        return True
    
    async def get_wait_time(self, user_id: str, provider: str) -> int:
        """Vraća koliko sekundi korisnik treba da čeka."""
        key = f"rate:{user_id}:{provider}"
        ttl = await self.redis.ttl(key)
        return max(0, ttl)
```

### 4.4.3 Request queue sistem

```python
class AIRequestQueue:
    """Queue sistem za AI request-e sa backoff-om."""
    
    async def enqueue(self, user_id: str, provider: str, task_func, *args):
        """Dodaje zadatak u queue."""
        # Koristi Celery za background processing
        task = task_func.delay(*args)
        return task.id
    
    async def wait_for_result(self, task_id: str, timeout: int = 300):
        """Čeka na rezultat sa timeout-om."""
        # Poll-uj Redis dok rezultat nije dostupan
        pass
    
    async def get_position(self, user_id: str) -> int:
        """Vraća poziciju u redu čekanja."""
        pass
```

---

# 5. MULTI-TENANT IZOLACIJA

## 5.1 User identification u request-u

### 5.1.1 Header-based autentifikacija

```python
# MCP server čita user_id iz headera
async def handle_mcp_request(request: Request):
    user_id = request.headers.get("X-User-ID")
    session_id = request.headers.get("X-Session-ID")
    api_key = request.headers.get("X-API-Key")  # za user-provided keys
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-ID header")
    
    # Prosledi user_id u tool handler
    return await process_tool_call(tool_name, params, user_id)
```

### 5.1.2 Tool parameter injection

```python
# Svaki tool automatski dobija user_id
Tool(
    name="quiz_list",
    description="List user's quizzes",
    inputSchema={
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User ID (auto-filled from session)"
            }
        }
    }
)

# U handler-u:
async def quiz_list_tool(user_id: str = None, ...):
    # Query filtrira po user_id - svaki korisnik vidi samo svoje kvizove
    quizzes = db.query(Quiz).filter(Quiz.user_id == user_id).all()
```

### 5.1.3 Resource-based routing

```
GET /api/v1/quizzes?user_id=123          # User 123's quizzes
GET /api/v1/documents?user_id=123        # User 123's documents
GET /api/v1/skills?user_id=123           # User 123's skills

# Ili u path-u:
GET /api/v1/users/123/quizzes
GET /api/v1/users/123/documents
GET /api/v1/users/123/skills
```

## 5.2 Dynamic Resources (Svaki user vidi samo svoje podatke)

### 5.2.1 Resource URIs

```python
# MCP Resources sa user-specific URIs
@server.list_resources()
async def list_resources(user_id: str) -> list[Resource]:
    return [
        Resource(
            uri=f"quizzes:///{user_id}/list",
            name=f"User {user_id} Quizzes",
            description="List of quizzes for this user"
        ),
        Resource(
            uri=f"documents:///{user_id}/list", 
            name=f"User {user_id} Documents",
            description="List of documents for this user"
        ),
        Resource(
            uri=f"skills:///{user_id}/list",
            name=f"User {user_id} Skills",
            description="List of skills for this user"
        ),
    ]
```

### 5.2.2 Query filtering

```python
# Svi database query-evi MORAJU filtrirati po user_id
async def quiz_list(user_id: str, filters: QuizFilters):
    query = db.query(Quiz)
    
    # OBAVEZNO - nikad ne dozvoli pristup tudjim podacima
    query = query.filter(Quiz.user_id == user_id)
    
    if filters.status:
        query = query.filter(Quiz.status == filters.status)
    
    return query.all()

# NIKAD ovako:
# return db.query(Quiz).all()  # GREŠKA - svi korisnici vide sve!
```

### 5.2.3 API endpoint primer

```python
# Primer sa header-based autentifikacijom
@app.get("/api/v1/quizzes")
async def list_quizzes(
    user_id: str = Header(X-User-ID, alias="x-user-id"),
    status: str = None
):
    # Auto-filter po user_id iz headera
    quizzes = await quiz_service.list_quizzes(
        user_id=user_id,
        status=status
    )
    return quizzes
```

## 5.3 Skill izolacija po korisniku

### 5.3.1 User-specific skills

```
user_id=123 → Skill: medical_document → Prompt template: "You are medical expert..."
user_id=456 → Skill: technical_manual → Prompt template: "You are technical analyst..."
```

### 5.3.2 Skill retrieval

```python
async def get_skill_for_user(user_id: str, document_category: str):
    # Prvo proveri korisnikove custom skills
    user_skill = db.query(Skill).filter(
        Skill.user_id == user_id,
        Skill.category == document_category,
        Skill.is_active == True
    ).first()
    
    if user_skill:
        return user_skill
    
    # Ako nema custom skill-a, koristi sistemski
    system_skill = db.query(Skill).filter(
        Skill.is_system == True,
        Skill.category == document_category
    ).first()
    
    return system_skill

# Apply skill prompt
def apply_skill_prompt(skill: Skill, content: str) -> str:
    prompt = skill.prompt_template
    
    # Inject content into prompt
    prompt += f"\n\nContent to analyze:\n{content}"
    
    # Add rules
    if skill.rules:
        prompt += f"\n\nRules: {json.dumps(skill.rules)}"
    
    return prompt
```

---

# 6. FAZA 1: Proširenje AI Providera

## 6.1 Novi Provideri za dodavanje

| Provider | API Endpoint | Tip | Zahtev |
|----------|--------------|-----|--------|
| **DeepSeek** | https://api.deepseek.com/v1/chat/completions | Chat | API Key |
| **Mistral** | https://api.mistral.ai/v1/chat/completions | Chat | API Key |
| **Grok** | https://api.x.ai/v1/chat/completions | Chat | API Key |
| **Gemini** | https://generativelanguage.googleapis.com/v1beta/models | Chat/Vision | API Key |

## 6.2 Detaljna implementacija za svaki provider

### 6.2.1 DeepSeek Client

```python
class DeepSeekClient(BaseTranslationClient):
    """Klijent za DeepSeek API."""
    
    COST_PER_1K_TOKENS = {
        "deepseek-chat": 0.001,  # $1/1M tokens input
        "deepseek-coder": 0.001,
    }
    
    RATE_LIMIT = 60  # requests per minute
    
    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.DEEPSEEK_API_KEY
        self.model = model or settings.DEEPSEEK_MODEL
        self.timeout = timeout or settings.DEEPSEEK_TIMEOUT
        self.base_url = "https://api.deepseek.com"
    
    @property
    def provider_name(self) -> str:
        return TranslationProvider.DEEPSEEK.value
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    def translate(self, text: str, source_language: str, target_language: str, context: Optional[str] = None) -> TranslationResult:
        # Implementacija koristi chat completions endpoint
        # Prompt: "Translate from {source} to {target}: {text}"
```

### 6.2.2 Mistral Client

```python
class MistralClient(BaseTranslationClient):
    """Klijent za Mistral API."""
    
    COST_PER_1K_TOKENS = {
        "mistral-small-latest": 0.0006,
        "mistral-medium-latest": 0.002,
        "mistral-large-latest": 0.002,
    }
    
    RATE_LIMIT = 50
    
    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.MISTRAL_API_KEY
        self.model = model or settings.MISTRAL_MODEL
        self.timeout = timeout or settings.MISTRAL_TIMEOUT
        self.base_url = "https://api.mistral.ai/v1"
```

### 6.2.3 Grok Client

```python
class GrokClient(BaseTranslationClient):
    """Klijent za xAI Grok API."""
    
    COST_PER_1K_TOKENS = {
        "grok-2": 0.002,
        "grok-2-vision": 0.002,
        "grok-beta": 0.005,
    }
    
    RATE_LIMIT = 60
    
    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.GROK_API_KEY
        self.model = model or settings.GROK_MODEL
        self.timeout = timeout or settings.GROK_TIMEOUT
        self.base_url = "https://api.x.ai/v1"
```

### 6.2.4 Gemini Client

```python
class GeminiClient(BaseTranslationClient):
    """Klijent za Google Gemini API."""
    
    COST_PER_1K_TOKENS = {
        "gemini-1.5-pro": 0.00125,
        "gemini-1.5-flash": 0.000075,
        "gemini-pro": 0.00025,
    }
    
    RATE_LIMIT = 15
    
    def __init__(self, api_key: str = None, model: str = None, timeout: int = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.timeout = timeout or settings.GEMINI_TIMEOUT
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
```

## 6.3 Settings proširenje

```python
# config.py additions
DEEPSEEK_API_KEY: Optional[str] = None
DEEPSEEK_MODEL: str = "deepseek-chat"
DEEPSEEK_TIMEOUT: int = 60
DEEPSEEK_RATE_LIMIT: int = 60  # requests per minute

MISTRAL_API_KEY: Optional[str] = None
MISTRAL_MODEL: str = "mistral-small-latest"
MISTRAL_TIMEOUT: int = 60
MISTRAL_RATE_LIMIT: int = 50

GROK_API_KEY: Optional[str] = None
GROK_MODEL: str = "grok-2"
GROK_TIMEOUT: int = 60
GROK_RATE_LIMIT: int = 60

GEMINI_API_KEY: Optional[str] = None
GEMINI_MODEL: str = "gemini-1.5-pro"
GEMINI_TIMEOUT: int = 60
GEMINI_RATE_LIMIT: int = 15
```

## 6.4 Enum proširenje

```python
class TranslationProvider(str, Enum):
    OLLAMA = "ollama"
    DEEPL = "deepl"
    OPENAI = "openai"
    GOOGLE = "google"
    CLAUDE = "claude"
    DEEPSEEK = "deepseek"        # NOVO
    MISTRAL = "mistral"          # NOVO
    GROK = "grok"                # NOVO
    GEMINI = "gemini"            # NOVO
```

---

# 7. FAZA 2: Skill Sistem (Prompt Šabloni)

## 7.1 Concept

Skill = Prompt template + pravila koji "upućuju" AI kako da koristi specifični PDF dokument.

## 7.2 Skill Model (baza)

```python
class Skill(Base):
    """Model za korisničke skills (prompt šablone)."""
    __tablename__ = "skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Kategorija dokumenta
    category = Column(String(50))  # legal, technical, medical, academic, general
    
    # Prompt template - glavni deo koji upućuje AI
    prompt_template = Column(Text, nullable=False)
    
    # Dodatna pravila
    rules = Column(JSON, default=dict)  # {
    #     "difficulty": "medium",
    #     "question_types": ["multiple_choice", "true_false"],
    #     "num_questions": 10,
    #     "focus_areas": ["definitions", "procedures"]
    # }
    
    # Tools koji su dozvoljeni za ovaj skill
    allowed_tools = Column(JSON, default=list)
    
    # Da li je sistemski skill (ne može se brisati)
    is_system = Column(Boolean, default=False)
    
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacije
    user = relationship("User", back_populates="skills")
```

## 7.3 Sistemski Skill Templates

```python
SYSTEM_SKILL_TEMPLATES = {
    "legal_document": {
        "name": "Legal Document Processor",
        "description": "Analyzes legal documents with numbered clauses and definitions",
        "category": "legal",
        "prompt_template": """
You are a legal document analyzer specialized in processing contracts, 
agreements, and legal texts.

When processing this PDF:
1. Identify numbered clauses (§1, §2, etc.) and articles
2. Extract key definitions and terminology
3. Note rights and obligations of parties
4. Identify deadlines, timelines, and important dates
5. Extract penalties and consequences

Quiz generation rules:
- Focus on key definitions and terms
- Create questions about rights and obligations
- Include questions about deadlines and timelines
- Multiple choice with 4 options (A, B, C, D)
- One correct answer
- Provide brief explanation for each answer
- Difficulty: medium to hard
""",
        "rules": {
            "difficulty": "medium",
            "question_types": ["multiple_choice", "true_false"],
            "num_questions": 10,
            "focus_areas": ["definitions", "obligations", "deadlines", "penalties"]
        }
    },
    
    "technical_manual": {
        "name": "Technical Manual Processor",
        "description": "Processes technical documentation and user manuals",
        "category": "technical",
        "prompt_template": """
You are a technical documentation expert specializing in user manuals,
API documentation, and technical specifications.

When processing this PDF:
1. Identify key concepts and terminology
2. Extract step-by-step procedures
3. Note configuration values and parameters
4. Identify error codes and troubleshooting steps
5. Extract best practices and recommendations

Quiz generation rules:
- Focus on procedures and workflows
- Create questions about configuration values
- Include questions about error handling
- Multiple choice with 4 options
- Include "NOT" questions to test deeper understanding
- Difficulty: medium
""",
        "rules": {
            "difficulty": "medium",
            "question_types": ["multiple_choice"],
            "num_questions": 8,
            "focus_areas": ["procedures", "configuration", "errors", "best_practices"]
        }
    },
    
    "medical_document": {
        "name": "Medical Document Processor",
        "description": "Processes medical literature and health documents",
        "category": "medical",
        "prompt_template": """
You are a medical documentation expert specializing in healthcare 
literature, clinical studies, and medical guides.

When processing this PDF:
1. Identify medical terminology and definitions
2. Extract symptoms and diagnosis information
3. Note treatment protocols and medications
4. Identify contraindications and side effects
5. Extract preventive measures

Quiz generation rules:
- Focus on accurate medical terminology
- Create questions about symptoms and treatments
- Include questions about drug interactions
- Multiple choice with 4 options
- Difficulty: hard (requires precise answers)
""",
        "rules": {
            "difficulty": "hard",
            "question_types": ["multiple_choice", "true_false"],
            "num_questions": 12,
            "focus_areas": ["terminology", "symptoms", "treatments", "contraindications"]
        }
    },
    
    "academic_paper": {
        "name": "Academic Paper Processor",
        "description": "Processes research papers and academic documents",
        "category": "academic",
        "prompt_template": """
You are an academic research expert specializing in scholarly papers
and scientific publications.

When processing this PDF:
1. Identify research methodology
2. Extract key findings and conclusions
3. Note statistical data and results
4. Identify research limitations
5. Extract future research directions

Quiz generation rules:
- Focus on research methodology
- Create questions about key findings
- Include questions about statistical significance
- Multiple choice with 4 options
- Difficulty: medium to hard
""",
        "rules": {
            "difficulty": "hard",
            "question_types": ["multiple_choice"],
            "num_questions": 10,
            "focus_areas": ["methodology", "findings", "statistics", "conclusions"]
        }
    },
    
    "general": {
        "name": "General Document Processor",
        "description": "Processes general documents and articles",
        "category": "general",
        "prompt_template": """
You are a general document analyzer.

When processing this PDF:
1. Identify main topics and themes
2. Extract key information and facts
3. Note important dates and numbers
4. Identify main arguments and points
5. Extract conclusions and summaries

Quiz generation rules:
- Focus on main ideas and key facts
- Create varied question types
- Include true/false questions
- Difficulty: easy to medium
""",
        "rules": {
            "difficulty": "medium",
            "question_types": ["multiple_choice", "true_false", "short_answer"],
            "num_questions": 10,
            "focus_areas": ["main_ideas", "key_facts", "conclusions"]
        }
    }
}
```

## 7.4 Skill Detection (Auto-detect)

```python
class SkillDetector:
    """Automatska detekcija tipa dokumenta."""
    
    CATEGORY_KEYWORDS = {
        "legal": ["contract", "agreement", "clause", "party", "obligation", "hereby", "whereas", "§", "article", "amend", "whereby", "hereinafter"],
        "technical": ["manual", "guide", "configuration", "api", "parameter", "specification", "install", "setup", "setup", "configure"],
        "medical": ["patient", "diagnosis", "treatment", "symptom", "medication", "clinical", "dosage", "contraindication", "prognosis", "etiology"],
        "academic": ["abstract", "methodology", "research", "findings", "conclusion", "hypothesis", "statistical", "significance", "sample", "variables"],
    }
    
    def detect_category(self, text: str) -> str:
        """Detektuje kategoriju dokumenta na osnovu teksta."""
        text_lower = text.lower()
        scores = {}
        
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            scores[category] = score
        
        if max(scores.values()) == 0:
            return "general"
        
        return max(scores, key=scores.get)
    
    async def get_skill_for_document(self, user_id: str, document_content: str) -> Skill:
        """Detektuje kategoriju i vraća odgovarajući skill za korisnika."""
        category = self.detect_category(document_content)
        
        # Prvo proveri korisnikove custom skills
        user_skill = db.query(Skill).filter(
            Skill.user_id == user_id,
            Skill.category == category,
            Skill.is_active == True
        ).first()
        
        if user_skill:
            return user_skill
        
        # Vrati sistemski skill
        return db.query(Skill).filter(
            Skill.is_system == True,
            Skill.category == category
        ).first()
```

---

# 8. FAZA 3: Quiz i Translation u Bazi

## 8.1 Proširenje Question Modela

```python
class Question(Base):
    # ... postojeća polja ...
    
    # Translation polja - NOVO
    original_text = Column(Text, nullable=False)  # Original question text (na originalnom jeziku)
    translated_text = Column(Text)  # Prevedeno pitanje (ako se razlikuje)
    
    # Jezičke informacije
    source_language = Column(String(10), default="en")  # Izvorni jezik teksta
    target_language = Column(String(10), default="sr")  # Ciljni jezik za prevod
    
    # Provider info za reproduktivnost
    translation_provider = Column(String(50))  # Koji provider je korišćen za prevod
    translation_model = Column(String(100))  # Model koji je korišćen
    
    # Metadata
    translation_metadata = Column(JSON, default=dict)  # {
    #     "tokens_used": 150,
    #     "cost": 0.001,
    #     "duration_ms": 2500,
    #     "api_call_success": True
    # }
    
    # Chunk source - iz kojeg chunk-a je pitanje generisano
    source_chunk_id = Column(UUID(as_uuid=True), ForeignKey("chunks.id"), nullable=True)
    source_chunk_content = Column(Text)  # Kopira sadržaj chunk-a za referencu
```

## 8.2 User API Credentials Model

```python
class UserAPICredential(Base):
    """Model za čuvanje korisničkih API ključeva."""
    __tablename__ = "user_api_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Provider informacije
    provider = Column(String(50), nullable=False)  # openai, deepseek, mistral, grok, gemini, claude
    
    # Enkriptovani podaci
    api_key_encrypted = Column(Text, nullable=False)  # Enkriptovan API key
    api_endpoint = Column(String(500))  # Custom endpoint (opciono)
    api_model = Column(String(100))  # Model name (opciono)
    
    # Dodatne informacije
    label = Column(String(100))  # User-defined label (e.g., "My OpenAI Key")
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)  # Da li je ovo primarni key
    
    # Usage tracking
    last_used_at = Column(DateTime(timezone=True))
    usage_count = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relacije
    user = relationship("User", back_populates="api_credentials")
```

## 8.3 Quiz Generation Flow sa User Keys

```
┌─────────────────────────────────────────────────────────────────┐
│                   QUIZ GENERATION FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. User Upload PDF                                            │
│         │                                                      │
│         ▼                                                      │
│  2. PDF Processing → Chunks (u bazu!)                         │
│         │                                                      │
│         ▼                                                      │
│  3. Skill Auto-Detection                                       │
│         │                                                      │
│         ▼                                                      │
│  4. User Select API Provider/Key                              │
│     (ili koristi sistemski default)                             │
│         │                                                      │
│         ▼                                                      │
│  5. Get User API Key from Vault                                │
│     (decrypt in memory only - NIKAD logovati!)                  │
│         │                                                      │
│         ▼                                                      │
│  6. Apply Skill Prompt Template                                │
│     (inject PDF content + rules)                                │
│         │                                                      │
│         ▼                                                      │
│  7. Call AI Provider (sa rate limiting)                       │
│     (with user's API key)                                       │
│         │                                                      │
│         ▼                                                      │
│  8. Parse Response → Questions                                  │
│         │                                                      │
│         ▼                                                      │
│  9. Translate Questions (if needed)                           │
│     (store original + translated)                               │
│         │                                                      │
│         ▼                                                      │
│  10. Save to Database                                          │
│      (with all metadata)                                        │
│         │                                                      │
│         ▼                                                      │
│  11. Return Quiz                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

# 9. FAZA 4: MCP Serveri

## 9.1 Arhitektura

```
┌─────────────────────────────────────────────────────────────────┐
│                    MCP GATEWAY SERVER                           │
│            (Jedna ulazna tačka - route-uje po domain-u)        │
│                                                                 │
│  Transport: Streamable HTTP (recommended for remote)           │
│  Port: 8080 (configurable)                                      │
│                                                                 │
│  Autentifikacija: X-User-ID header u svakom request-u           │
└─────────────────────────────────────────────────────────────────┘
         │              │              │
         ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  QUIZ MCP   │ │ TRANSLATE   │ │  DOCUMENT   │
│  SERVER     │ │   MCP       │ │   MCP       │
│             │ │  SERVER     │ │   SERVER    │
└─────────────┘ └─────────────┘ └─────────────┘
```

## 9.2 Quiz MCP Server

### Tools:

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="quiz_create",
            description="Create a new quiz from document with AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {"type": "string", "description": "Document ID"},
                    "title": {"type": "string", "description": "Quiz title"},
                    "num_questions": {"type": "integer", "default": 10},
                    "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
                    "skill_id": {"type": "string", "description": "Optional skill ID to use"},
                    "api_provider": {"type": "string", "enum": ["ollama", "openai", "deepseek", "mistral", "grok", "gemini"]},
                    "use_user_key": {"type": "boolean", "default": False, "description": "Use user's API key"}
                },
                "required": ["document_id", "title"]
            }
        ),
        Tool(
            name="quiz_generate_questions",
            description="Generate questions from document chunks",
            inputSchema={...}
        ),
        Tool(
            name="quiz_translate",
            description="Translate quiz questions to target language",
            inputSchema={...}
        ),
        Tool(
            name="quiz_get_by_id",
            description="Get quiz by ID with questions",
            inputSchema={...}
        ),
        Tool(
            name="quiz_list",
            description="List user's quizzes",
            inputSchema={...}
        ),
        Tool(
            name="quiz_delete",
            description="Delete a quiz",
            inputSchema={...}
        ),
        Tool(
            name="quiz_analyze_performance",
            description="Analyze quiz performance and generate insights",
            inputSchema={...}
        ),
    ]
```

## 9.3 Translate MCP Server

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="translate_text",
            description="Translate text from source to target language",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "source_language": {"type": "string", "default": "en"},
                    "target_language": {"type": "string", "default": "sr"},
                    "provider": {"type": "string"},
                    "use_user_key": {"type": "boolean", "default": False}
                },
                "required": ["text", "target_language"]
            }
        ),
        Tool(
            name="translate_batch",
            description="Translate multiple texts in batch",
            inputSchema={...}
        ),
        Tool(
            name="translate_document",
            description="Translate entire document",
            inputSchema={...}
        ),
        Tool(
            name="translate_get_providers",
            description="Get available translation providers",
            inputSchema={...}
        ),
    ]
```

## 9.4 Document MCP Server

```python
@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="document_process_pdf",
            description="Process PDF and extract chunks",
            inputSchema={...}
        ),
        Tool(
            name="document_get_chunks",
            description="Get document chunks",
            inputSchema={...}
        ),
        Tool(
            name="document_search",
            description="Search within document",
            inputSchema={...}
        ),
        Tool(
            name="document_get_skills",
            description="Get available skills for document processing",
            inputSchema={...}
        ),
        Tool(
            name="document_detect_category",
            description="Detect document category/type",
            inputSchema={...}
        ),
    ]
```

---

# 10. FAZA 5: User API Key Security

## 10.1 Enkripcija

```python
from cryptography.fernet import Fernet
import base64
import hashlib
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class APIKeyVault:
    """Secure vault za čuvanje korisničkih API ključeva."""
    
    def __init__(self, master_key: str):
        # Derive key from master key using SHA256
        key = hashlib.sha256(master_key.encode()).digest()
        self.cipher = Fernet(base64.urlsafe_b64encode(key))
    
    def encrypt(self, api_key: str) -> str:
        """Enkriptuje API key."""
        return self.cipher.encrypt(api_key.encode()).decode()
    
    def decrypt(self, encrypted_key: str) -> str:
        """Dekriptuje API key."""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
    
    def is_valid_key_format(self, provider: str, api_key: str) -> bool:
        """Validira format API key-a za specifičnog provajdera."""
        validations = {
            "openai": lambda k: k.startswith("sk-") and len(k) > 20,
            "deepseek": lambda k: k.startswith("sk-") and len(k) > 20,
            "mistral": lambda k: k.startswith("sk-") and len(k) > 20,
            "grok": lambda k: k.startswith("xai-") and len(k) > 20,
            "gemini": lambda k: len(k) > 30,
            "claude": lambda k: k.startswith("sk-ant") and len(k) > 30,
        }
        return validations.get(provider, lambda k: True)(api_key)
```

## 10.2 Request Flow

```
User Request (with user_id in context)
        │
        ▼
MCP Server receives tool call
        │
        ▼
Validate user session
        │
        ▼
Lookup encrypted API key from database
        │
        ▼
Decrypt key (in memory only - NEVER LOG!)
        │
        ▼
Validate key format
        │
        ▼
Check rate limits (per user, per provider)
        │
        ▼
Make API call to provider
        │
        ▼
Return result (never log the key)
        │
        ▼
Update usage statistics
```

## 10.3 Security Best Practices

1. **Key never leaves memory decrypted** - Samo za vreme API poziva
2. **No key logging** - Čak ni u error logovima
3. **Key validation** - Proveri format pre korišćenja
4. **Rate limiting** - Po korisniku, po provideru
5. **Usage tracking** - Token count, cost estimation
6. **Audit log** - Ko je kada koristio koji key

---

# 11. FAZA 6: Implementation Steps

## Korak 1: Database Migration

```sql
-- user_api_credentials table
CREATE TABLE user_api_credentials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    api_endpoint VARCHAR(500),
    api_model VARCHAR(100),
    label VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- skills table
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50),
    prompt_template TEXT NOT NULL,
    rules JSONB DEFAULT '{}',
    allowed_tools JSONB DEFAULT '[]',
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add translation fields to questions table
ALTER TABLE questions ADD COLUMN original_text TEXT NOT NULL;
ALTER TABLE questions ADD COLUMN translated_text TEXT;
ALTER TABLE questions ADD COLUMN source_language VARCHAR(10) DEFAULT 'en';
ALTER TABLE questions ADD COLUMN target_language VARCHAR(10) DEFAULT 'sr';
ALTER TABLE questions ADD COLUMN translation_provider VARCHAR(50);
ALTER TABLE questions ADD COLUMN translation_model VARCHAR(100);
ALTER TABLE questions ADD COLUMN translation_metadata JSONB DEFAULT '{}';
ALTER TABLE questions ADD COLUMN source_chunk_id UUID REFERENCES chunks(id);
ALTER TABLE questions ADD COLUMN source_chunk_content TEXT;
```

## Korak 2: AI Provideri

- Kreirati `DeepSeekClient`, `MistralClient`, `GrokClient`, `GeminiClient` klase
- Dodati rate limiting u svaki client
- Dodati u `TranslationService._clients` dictionary
- Update `TranslationProvider` enum
- Dodati u config.py sa rate limit settings

## Korak 3: API Key Management + Multi-Tenant

- Kreirati `UserAPICredentialService`
- Implementirati enkripciju sa `APIKeyVault`
- Kreirati API endpoint-e sa X-User-ID header autentifikacijom
- Implementirati rate limiter
- Kreirati audit log

## Korak 4: Skill System

- Kreirati `SkillService`
- Implementirati auto-detection sa `SkillDetector`
- Kreirati skill CRUD endpoint-e
- Seed-ovati sistemske skill templates

## Korak 5: MCP Servers

- Kreirati `quiz-mcp-server` sa user_id u tool-ovima
- Kreirati `translate-mcp-server`
- Kreirati `document-mcp-server`
- Implementirati middleware za X-User-ID ekstrakciju
- Implementirati rate limiting po useru
- Testirati sa MCP Inspector

## Korak 6: Integration

- Povezati Chat sa MCP gateway
- Dodati user API key selection u UI
- Testirati end-to-end flow
- Performance test sa 1000+ korisnika

---

# 12. TEHNIČKA DOKUMENTACIJA

## 12.1 Dependencies

```txt
# MCP Server
mcp>=0.5.0
mcp[cli]>=0.5.0

# Cryptography
cryptography>=41.0.0

# AI Providers (novi)
anthropic>=0.18.0
google-generativeai>=0.3.0
mistralai>=0.1.0
deepseek>=0.1.0

# Rate limiting
redis>=5.0.0
aioredis>=2.0.0

# Async
httpx>=0.27.0  # Async HTTP client
```

## 12.2 Environment Variables

```bash
# MCP Server
MCP_SERVER_PORT=8080
MCP_SERVER_HOST=0.0.0.0
MCP_TRANSPORT=http
MCP_RATE_LIMIT_ENABLED=true

# Security
ENCRYPTION_MASTER_KEY=your-master-key-here

# Rate Limits (requests per minute per user)
DEFAULT_RATE_LIMIT=60
OPENAI_RATE_LIMIT=100
DEEPSEEK_RATE_LIMIT=60
MISTRAL_RATE_LIMIT=50
GROK_RATE_LIMIT=60
GEMINI_RATE_LIMIT=15

# Default providers
DEFAULT_OLLAMA_HOST=http://localhost:11434
DEFAULT_OPENAI_MODEL=gpt-4
```

## 12.3 Docker Compose proširenje

```yaml
# Dodati u docker-compose.yml za skaliranje
services:
  mcp-gateway:
    image: ai-learning-mcp-gateway
    ports:
      - "8080:8080"
    environment:
      - MCP_SERVER_PORT=8080
      - ENCRYPTION_MASTER_KEY=${ENCRYPTION_MASTER_KEY}
    depends_on:
      - redis
      - db
    deploy:
      replicas: 2  # Više instanci za 1000+ korisnika
    
  mcp-quiz:
    image: ai-learning-quiz-mcp
    deploy:
      replicas: 4
    
  mcp-translate:
    image: ai-learning-translate-mcp  
    deploy:
      replicas: 4

  worker:
    image: ai-learning-worker
    deploy:
      replicas: 8  # Više workera za AI request-e
```

---

# 13. PRILOZI

## A. Tool Response Format (JSON)

```json
{
  "success": true,
  "data": {
    "quiz_id": "uuid",
    "title": "Quiz Title",
    "questions": [
      {
        "id": "uuid",
        "question_text": "What is...?",
        "translated_text": "Šta je...?",
        "options": ["A", "B", "C", "D"],
        "correct_answer": "A",
        "translation_provider": "deepseek",
        "translation_model": "deepseek-chat"
      }
    ],
    "translation_metadata": {
      "total_tokens": 1500,
      "total_cost": 0.015,
      "duration_ms": 5000
    }
  },
  "user_id": "user-uuid",
  "rate_limit_remaining": 45
}
```

## B. Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded for provider deepseek",
    "retry_after_seconds": 30,
    "details": {
      "provider": "deepseek",
      "limit": 60,
      "used": 60
    }
  }
}
```

## C. MCP Request sa User ID

```json
{
  "jsonrpc": "2.0",
  "id": "req-123",
  "method": "tools/call",
  "params": {
    "name": "quiz_create",
    "arguments": {
      "document_id": "doc-uuid",
      "title": "My Quiz"
    },
    "_meta": {
      "user_id": "user-uuid",
      "session_id": "session-uuid"
    }
  }
}
```

---

# VERZIJA DOKUMENTA

- **Verzija**: 1.1.0
- **Datum**: April 2026
- **Autor**: AI Learning System Team
- **Status**: Plan za implementaciju (Ažurirano sa skaliranjem i multi-tenant izolacijom)

---

**Kraj dokumenta.**
