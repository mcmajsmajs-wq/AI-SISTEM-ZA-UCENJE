# AI LEARNING SYSTEM

Personalizovana aplikacija za učenje koja automatizuje proces konverzije stručnih PDF materijala na srpski jezik, generiše materijale za proveru znanja (kvizovi, PDF, DOCX, PPTX, XLSX) i inteligentno upravlja tempom učenja kroz planiranje i analitiku.

## Arhitektura

```
[Browser] → [Nginx :8090] → [FastAPI :8010] → [PostgreSQL :5432]
                                               → [Redis :6379]
                                               → [MinIO :9002]
                                               → [Ollama :11434]
              [Celery Worker] ← [Redis (broker)]
```

## Tehnologije

- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Celery, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: PostgreSQL 15, Redis 7
- **AI**: Ollama, OpenAI, Claude, DeepSeek, Groq, Mistral
- **Storage**: MinIO (S3-compatible)
- **Export**: ReportLab (PDF), python-docx, python-pptx, openpyxl
- **PDF**: PyMuPDF, Tesseract OCR
- **Testing**: pytest, pytest-cov (~587 testova, 60%+ coverage)
- **Monitoring**: Prometheus, Grafana

## Servisi

| Servis | Port | Opis |
|--------|------|------|
| FastAPI | 8010 | REST API + Swagger UI `/docs` |
| Frontend | 8090 | Web aplikacija (Nginx) |
| PostgreSQL | 5432 | Baza podataka |
| Redis | 6379 | Cache & Celery broker |
| MinIO | 9002 | File storage |
| Grafana | 3000 | Monitoring dashboards |
| Ollama | 11434 | Lokalni AI LLM |

## Brzi početak

```bash
cd /home/dju/projects/ai-learning
docker compose -f docker/docker-compose.yml up -d
docker compose exec app alembic upgrade head
```

Otvorite `http://localhost:8090`.

## Dokumentacija

Sva dokumentacija je organizovana u `docs/` direktorijumu:

| Direktorijum | Sadržaj |
|-------------|---------|
| `docs/user/` | UPUTSTVO_ZA_UPOTREBU.md — uputstvo za korisnike |
| `docs/developer/` | DEVELOPER_GUIDE.md — vodič za developere, PRILOG_PROMPT_TEMPLATES.md |
| `docs/operations/` | CI_CD_STRATEGIJA.md, INSTALLATION_GUIDE.md |
| `docs/security/` | SECURITY.md |
| `docs/plans/` | Planovi: MCP integracija, optimizacije, implementacija |
| `docs/reference/` | CHANGELOG.md, SRPSKI_PRIRUCNIK.md, DEPENDENCIES_STATUS.md, BACKUP_DESIGN.md |
| `docs/archive/` | Istorijske analize i stara dokumentacija |

## Makefile komande

```bash
make up              # Start all services
make down            # Stop all services
make dev             # Start development
make test            # Run tests
make logs            # View logs
make verify          # Full system verification
```

## API Endpointi (osnovni)

- `POST /api/v1/auth/register` — Registracija
- `POST /api/v1/auth/login` — Login
- `POST /api/v1/documents` — Kreiraj dokument
- `GET /api/v1/documents` — Lista dokumenata
- `POST /api/v1/documents/{id}/process` — Obrada PDF-a
- `POST /api/v1/documents/{id}/translate` — Prevod
- `POST /api/v1/documents/{id}/pipeline` — Auto Pipeline (PDF→prevod→kviz)
- `GET /api/v1/documents/{id}/export/pdf` — PDF export
- `POST /api/v1/quizzes` — Kreiraj kviz
- `POST /api/v1/quizzes/{id}/attempts` — Započni kviz
- `POST /api/v1/quizzes/{id}/attempts/{aid}/submit` — Predaj odgovore

## Licenca

MIT License
