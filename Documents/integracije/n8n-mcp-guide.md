# MCP Server Integration with n8n - NucBoxM5PLUS

## Lokalni Server Info

| Parametar | Vrednost |
|-----------|----------|
| **Hostname** | `NucBoxM5PLUS` |
| **Lokalna IP** | `192.168.1.16` |
| **WSL IP** | `10.88.0.1` |
| **Korisnik** | `dju` |
| **Home** | `/home/dju` |
| **Platform** | WSL2 (Windows) |

---

## Arhitektura

```
┌─────────────────────────────────────────────────────────────┐
│                  n8n na NucBoxM5PLUS                         │
│                  (192.168.1.16)                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │
│  │1.HTTP Trigger │  │2.Cron Health │  │3.SSH Trigger │  │
│  │POST /mcp/exec │  │Check (1sat) │  │POST /mcp/ssh │  │
│  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘  │
│          │                  │                  │              │
│          └──────────────────┼──────────────────┘              │
│                             ▼                                 │
│                   Build Command (Auto-detect)                  │
│                             │                                 │
│          ┌─────────────────┴─────────────────┐             │
│          ▼                                       ▼             │
│   ┌─────────────┐                        ┌─────────────┐   │
│   │Local vs NPX│                        │  SSH Node   │   │
│   └──────┬─────┘                        └──────┬──────┘   │
│          │                                       │            │
│     ┌────┴────┐                                 │            │
│     ▼         ▼                                 │            │
│  ┌──────┐ ┌──────┐                           │            │
│  │Local │ │ NPX  │                           │            │
│  │Exec  │ │Exec  │                           │            │
│  └──────┘ └──────┘                           │            │
│          └─────────────────┬───────────────────┘            │
│                            ▼                                │
│                    Format Response                           │
│                            │                                │
│                    ┌──────┴──────┐                        │
│                    ▼             ▼                        │
│              Respond OK    Respond Err                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### POST /webhook/mcp/execute

**Lokalni MCP serveri:**

```bash
# AI Learning System - Health Check
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"server": "ai-learning", "tool": "health_check"}'

# Moj Ubuntu - Sistem
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"server": "moj-ubuntu", "tool": "proveri_sistem"}'

# HPE OneView - Serveri
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"server": "hpe-oneview", "tool": "proveri_servere"}'
```

**NPX MCP serveri:**

```bash
# Brave Search
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "server": "brave-search",
    "tool": "brave_web_search",
    "arguments": {"query": "MCP protocol", "count": 5}
  }'

# Firecrawl - Scrape
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "server": "firecrawl",
    "tool": "scrape",
    "arguments": {"url": "https://example.com", "formats": ["markdown"]}
  }'

# Docker
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"server": "docker", "tool": "list_containers", "arguments": {"all": true}}'

# Sequential Thinking
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{
    "server": "sequential-thinking",
    "tool": "sequentialthinking",
    "arguments": {
      "thought": "Analyzing this problem...",
      "thoughtNumber": 1,
      "totalThoughts": 5,
      "nextThoughtNeeded": true
    }
  }'
```

### POST /webhook/mcp/ssh

**SSH na lokalni server:**

```bash
# Docker status
curl -X POST http://localhost:5678/webhook/mcp/ssh \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "username": "dju",
    "command": "docker ps --format \"table {{.Names}}\t{{.Status}}\""
  }'

# System info
curl -X POST http://localhost:5678/webhook/mcp/ssh \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "username": "dju",
    "command": "htop"
  }'

# Disk usage
curl -X POST http://localhost:5678/webhook/mcp/ssh \
  -H "Content-Type: application/json" \
  -d '{
    "host": "localhost",
    "username": "dju",
    "command": "df -h"
  }'
```

---

## Auto-Detection

Ako ne navedete `server`, workflow auto-detektuje based na tool imenu:

| Tool keyword | Server |
|-------------|--------|
| `docker`, `container` | docker |
| `brave`, `search` | brave-search |
| `sequential` | sequential-thinking |
| `scrape`, `crawl`, `firecrawl` | firecrawl |
| `pdf`, `docx`, `markdown` | markdownify |
| `playwright`, `browser` | playwright |
| `server`, `hardware`, `oneview` | hpe-oneview |
| `system`, `cpu`, `disk`, `procesi` | moj-ubuntu |
| (default) | ai-learning |

**Primer bez servera:**
```bash
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "brave_web_search", "arguments": {"query": "MCP"}}'
```

---

## Lokalni MCP Serveri

| Server | Putanja | Opis |
|--------|---------|------|
| **ai-learning** | `/home/dju/mojAiProjekat/New folder/mcp-server/` | AI Learning System |
| **ai-learning-alt** | `/home/dju/moji projekti/AI SISTEM ZA UCENJE/ai-learning-system/mcp-server/` | AI Learning (alt) |
| **moj-ubuntu** | `/home/dju/mcp-servers/moj-ubuntu-server/` | Ubuntu monitoring |
| **hpe-oneview** | `/home/dju/moji projekti/MCP_HpOneView/` | HPE infrastructure |

## NPX MCP Serveri

| Server | Package | Opis |
|--------|---------|------|
| **brave-search** | `@modelcontextprotocol/server-brave-search` | Web search |
| **sequential-thinking** | `@modelcontextprotocol/server-sequential-thinking` | Problem solving |
| **firecrawl** | `firecrawl-mcp` | Web scraping |
| **docker** | `mcp-docker-server` | Docker management |
| **markdownify** | `mcp-markdownify-server` | File conversion |
| **playwright** | `@playwright/mcp` | Browser automation |
| **n8n** | `n8n-mcp` | n8n workflow |
| **gmail** | `@gongrzhe/server-gmail-autoauth-mcp` | Gmail API |

---

## Environment Variables

Dodajte u n8n ili sistem:

```bash
# API Keys
export BRAVE_API_KEY="your_brave_api_key"
export FIRECRAWL_API_KEY="your_firecrawl_api_key"
```

---

## Primeri Response

**Success:**
```json
{
  "success": true,
  "executionId": "mcp-m1abc123",
  "server": "ai-learning",
  "tool": "health_check",
  "result": "All services healthy: API ✓, Database ✓, Redis ✓",
  "executionTime": "234ms",
  "timestamp": "2026-03-22T10:30:00.000Z"
}
```

**Error:**
```json
{
  "success": false,
  "error": "Container not found",
  "server": "docker",
  "tool": "container_logs",
  "timestamp": "2026-03-22T10:30:00.000Z"
}
```

---

## Cron Health Check

Automatski se pokreće svaki sat:

| Server | Tool |
|--------|------|
| ai-learning | `health_check` |
| moj-ubuntu | `proveri_sistem` |
| hpe-oneview | `proveri_servere` |

---

## Lokalni Test

```bash
# Test HTTP endpoint
curl -X POST http://localhost:5678/webhook/mcp/execute \
  -H "Content-Type: application/json" \
  -d '{"server": "moj-ubuntu", "tool": "proveri_sistem"}'

# Test SSH endpoint
curl -X POST http://localhost:5678/webhook/mcp/ssh \
  -H "Content-Type: application/json" \
  -d '{"command": "echo hello"}
```

---

*Generisano: 2026-03-22 | Server: NucBoxM5PLUS (192.168.1.16)*
