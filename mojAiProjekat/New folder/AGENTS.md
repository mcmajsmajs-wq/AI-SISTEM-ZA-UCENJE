# AGENTS.md - AI Learning Sistem

## Dostupni Skill-ovi

Koristi `/skill` komandu za učitavanje specifičnih skill-ova:

| Skill | Komanda | Opis |
|-------|---------|------|
| ai-learning-dev | `/skill ai-learning-dev` | Opšti razvoj, backend, frontend |
| ai-learning-db | `/skill ai-learning-db` | Database, migracije, backup |
| ai-learning-mcp | `/skill ai-learning-mcp` | MCP Server, tool-ovi |
| ai-learning-docker | `/skill ai-learning-docker` | Docker, container-i, logovi |
| ai-learning-debug | `/skill ai-learning-debug` | Troubleshooting, health check |
| ai-learning-test | `/skill ai-learning-test` | Testiranje - backend, API, E2E |

## Projekat Struktura

```
/home/dju/mojAiProjekat/New folder/
├── backend/          # FastAPI + SQLAlchemy
├── frontend/         # TypeScript + Vite
├── mcp-server/      # MCP Server
├── docker/           # Docker konfiguracija
├── scripts/         # Pomocne skripte
└── .opencode/       # OpenCode konfiguracija
```

## Česte Komande

### Development
```bash
cd /home/dju/mojAiProjekat/New\ folder
make dev          # Start development
make test         # Run tests
```

### Docker
```bash
make up           # Start all services
make down         # Stop all services
make logs         # View logs
```

### Database
```bash
alembic upgrade head           # Migracije
docker exec -it ai-learning-db psql -U ai_learning_user -d ai_learning_db
```

## Servisi

| Servis | Port | Opis |
|--------|------|------|
| Backend API | 8010 | FastAPI |
| Frontend | 8083 | Nginx |
| Database | 5432 | PostgreSQL |
| Redis | 6379 | Cache |
| MinIO | 9002 | S3 Storage |

## Kada Koristiti

- **ai-learning-dev**: Razvoj novih feature-a, API endpoint-a, modela
- **ai-learning-db**: Database promene, migracije, provera podataka
- **ai-learning-mcp**: Rad sa MCP serverom
- **ai-learning-docker**: Start/stop servisa, logovi
- **ai-learning-debug**: Nešto ne radi, health check
- **ai-learning-test**: Testiranje svih delova sistema

## Dokumentacija

Detaljno uputstvo: [OPENCODE_SKILLS_GUIDE.md](./OPENCODE_SKILLS_GUIDE.md)

---

Za više informacija o OpenCode skill-ovima: https://opencode.ai/docs/skills/
