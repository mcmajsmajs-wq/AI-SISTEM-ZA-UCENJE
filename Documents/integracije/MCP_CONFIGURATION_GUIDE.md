# MCP Servers Configuration Guide

## Overview

Ova konfiguracija ukljucuje 11 MCP servera. Svaki zahteva odredjene tokene/API kljuceve.

---

## 1. GitHub MCP
**Status:** Konfigurisan  
**Package:** `@modelcontextprotocol/server-github`  
**Token:** GitHub Personal Access Token

### Kako dobiti token:
1. Idi na https://github.com/settings/tokens
2. Klikni "Generate new token (classic)"
3. Izaberi scopes: `repo`, `read:user`, `workflow`
4. Kopiraj token

### Postavi token:
```bash
# U opencode.json, zameni:
"GITHUB_PERSONAL_ACCESS_TOKEN": "tvoj_token"
```

---

## 2. Brave Search MCP
**Status:** Konfigurisan  
**Package:** `@modelcontextprotocol/server-brave-search`  
**Token:** Brave Search API Key

### Kako dobiti token:
1. Idi na https://brave.com/search/api/
2. Napravi nalog i izaberi plan (Free tier: 2000 upita/mesečno)
3. Idi na Dashboard > API Keys
4. Kopiraj API key

### Postavi token:
```bash
export BRAVE_API_KEY="tvoj_brave_api_key"
```

---

## 3. Docker MCP
**Status:** Konfigurisan  
**Package:** `mcp-docker-server`  
**Token:** Nije potreban (lokalni Docker daemon)

### Zahtevi:
- Docker Desktop ili Docker Engine instaliran
- Docker daemon mora biti pokrenut

### Provera:
```bash
docker ps  # Treba da pokaze listu container-a
```

---

## 4. Firecrawl MCP
**Status:** Konfigurisan  
**Package:** `firecrawl-mcp`  
**Token:** Firecrawl API Key

### Kako dobiti token:
1. Idi na https://www.firecrawl.dev/
2. Napravi nalog
3. Idi na Dashboard > API Keys
4. Kopiraj API key

### Postavi token:
```bash
export FIRECRAWL_API_KEY="tvoj_firecrawl_api_key"
```

---

## 5. Sequential Thinking MCP
**Status:** Konfigurisan  
**Package:** `@modelcontextprotocol/server-sequential-thinking`  
**Token:** Nije potreban

Ovo je lokalni server za strukturalno razmisljanje. Nema external dependencies.

---

## 6. Gmail MCP
**Status:** Konfigurisan  
**Package:** `@gongrzhe/server-gmail-autoauth-mcp`  
**Token:** Google OAuth2 Credentials

### Kako dobiti credentials:
1. Idi na https://console.cloud.google.com/
2. Napravi novi project ili izaberi postojeci
3. Omoguci Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
4. Idi na Credentials > Create Credentials > OAuth client ID
5. Application type: Desktop app
6. Skini JSON i izvadi `client_id` i `client_secret`

### Postavi credentials:
```bash
export GMAIL_CLIENT_ID="tvoj_client_id.apps.googleusercontent.com"
export GMAIL_CLIENT_SECRET="tvoj_client_secret"
```

### Dodatna setup:
Trebat ces i OAuth tokene za pristup. Prvi put kad pokrenes, otvorice se browser za autorizaciju.

---

## 7. Markdownify MCP
**Status:** Konfigurisan  
**Package:** `mcp-markdownify-server`  
**Token:** OpenAI API Key (za neke konverzije)

### Kako dobiti token:
1. Idi na https://platform.openai.com/api-keys
2. Napravi novi API key
3. Kopiraj key

### Postavi token:
```bash
export OPENAI_API_KEY="sk-tvoj_api_key"
```

### Alternative:
Mozes koristiti i druge API provajdere. Proveri markdownify dokumentaciju za detalje.

---

## 8. n8n MCP
**Status:** Konfigurisan  
**Package:** `n8n-mcp`  
**Token:** n8n API Key

### Zahtevi:
- n8n instanca mora biti pokrenuta na localhost:5678

### Kako dobiti API key:
1. Otvori n8n (http://localhost:5678)
2. Idi na Settings > API
3. Generisi API key

### Postavi:
```bash
export N8N_URL="http://localhost:5678"
export N8N_API_KEY="tvoj_n8n_api_key"
```

---

## 9. Playwright MCP
**Status:** Konfigurisan  
**Token:** Nije potreban

Trebace ti instaliran Playwright:
```bash
npx playwright install chromium
```

---

## 10. Moj Ubuntu MCP
**Status:** Konfigurisan  
**Token:** Nije potreban

Lokalni MCP server za Ubuntu komande.

---

## 11. Awesome Copilot
**Status:** Konfigurisan  
**Token:** Zavisno od implementacije

---

## Environment Variables Setup

Kreiraj `.env` fajl u `/home/dju/` sa sledecim:

```bash
# GitHub
GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxxxxxxxxxx

# Brave Search
BRAVE_API_KEY=BSAxxxxxxxxxxxx

# Firecrawl
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxx

# Gmail (Google Cloud Console)
GMAIL_CLIENT_ID=xxxxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=xxxxx

# OpenAI (za Markdownify)
OPENAI_API_KEY=sk-xxxxx

# n8n
N8N_API_KEY=xxxxx
```

### Ucitavanje env variables:
```bash
# Dodaj u ~/.bashrc ili ~/.zshrc:
source ~/.env  # (ako koristis direnv ili manualno)
```

### Ili direktno u terminalu:
```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="tvoj_token"
export BRAVE_API_KEY="tvoj_brave_key"
# itd.
```

---

## Restartovanje opencode

Nakon postavljanja tokena, restartuj opencode:

```bash
# Zaustavi opencode (Ctrl+C ili q)
# Ponovo pokreni:
opencode
```

---

## Troubleshooting

### Docker MCP ne radi:
```bash
# Proveri Docker status:
sudo systemctl status docker

# Dodaj sebe u docker grupu:
sudo usermod -aG docker $USER
newgrp docker
```

### Gmail auth problemi:
- Prvi put ce se otvoriti browser za autorizaciju
- Skladišti se u `~/.config/gmail-mcp/credentials.json`

### n8n connection refused:
```bash
# Proveri da li n8n radi:
curl http://localhost:5678
```

---

## Linkovi za dokumentaciju

- Brave Search API: https://brave.com/search/api/
- Firecrawl: https://docs.firecrawl.dev/
- Gmail API: https://developers.google.com/gmail/api
- n8n: https://docs.n8n.io/
- Model Context Protocol: https://modelcontextprotocol.io/

---

## Datum konfiguracije: 2026-03-20
