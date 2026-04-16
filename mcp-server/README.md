# AI Learning System MCP Server

MCP (Model Context Protocol) server za monitoring i upravljanje AI Learning System projektom.

## Funkcionalnosti

### Tools (Alati)

| Tool | Opis |
|------|------|
| `docker_status` | Status svih Docker kontejnera |
| `docker_logs` | Logovi za određeni servis |
| `docker_restart` | Restart određenog servisa |
| `health_check` | Health check svih servisa |
| `api_docs` | API dokumentacija i endpoint-i |
| `read_config` | Čitanje .env konfiguracije |
| `project_status` | Status implementacije projekta |
| `dependencies_check` | Status Python dependencies |
| `ollama_status` | Status Ollama i dostupni modeli |
| `pull_ollama_model` | Uputstvo za preuzimanje AI modela |

### Resources (Resursi)

- Project README
- Dependencies Status
- Missing Features (NEDOSTAJUCE_STVARI.md)
- Installation Guide
- Log fajlovi

## Instalacija

### Opcija 1: pip

```bash
cd /path/to/your/project/mcp-server
pip install -e .
```

### Opcija 2: UV (preporučeno)

```bash
cd /path/to/your/project/mcp-server
uv pip install -e .
```

## Konfiguracija

Dodajte u vaš MCP klijent konfiguraciju (npr. Claude Desktop, Cursor, itd.):

```json
{
  "mcpServers": {
    "ai-learning": {
      "command": "python",
      "args": ["-m", "ai_learning_mcp"],
      "env": {
        "PROJECT_ROOT": "/path/to/your/project",
        "API_BASE_URL": "http://localhost:8010"
      }
    }
  }
}
```

Ili koristeći UVX:

```json
{
  "mcpServers": {
    "ai-learning": {
      "command": "uvx",
      "args": ["--directory", "/path/to/your/project/mcp-server", "ai-learning-mcp"],
      "env": {
        "PROJECT_ROOT": "/path/to/your/project",
        "API_BASE_URL": "http://localhost:8010"
      }
    }
  }
}
```

## Environment Variables

| Variable | Default | Opis |
|----------|---------|------|
| `API_BASE_URL` | `http://localhost:8010` | URL FastAPI aplikacije |
| `PROJECT_ROOT` | (auto-detect) | Putanja do projekta (gde je docker-compose.yml) |

## Primeri korišćenja

### Provera statusa Docker kontejnera

```
User: Pokaži mi status svih Docker kontejnera
AI: [koristi docker_status tool]
```

### Čitanje logova

```
User: Prikaži mi poslednjih 100 linija logova za app servis
AI: [koristi docker_logs tool sa service="app", lines=100]
```

### Health check

```
User: Proveri da li svi servisi rade
AI: [koristi health_check tool]
```

### Restart servisa

```
User: Restartuj worker servis
AI: [koristi docker_restart tool sa service="worker"]
```

## Razvoj

### Pokretanje lokalno

```bash
cd mcp-server
python -m ai_learning_mcp
```

### Testiranje

```bash
pytest tests/
```

## Struktura projekta

```
mcp-server/
├── src/
│   └── ai_learning_mcp/
│       ├── __init__.py      # Glavni server kod
│       └── __main__.py      # Entry point
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Troubleshooting

### "command not found: docker"

Dodajte korisnika u docker grupu:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### "Connection refused"

Proverite da li Docker kontejneri rade:
```bash
docker compose -f docker/docker-compose.yml ps
```

### "Module not found: mcp"

Instalirajte MCP:
```bash
pip install mcp
```
