# OpenCode MCP Integracija

## Preuzimanje

Kloniraj repozitorijum:
```bash
git clone https://github.com/your-repo/MCP_Servers.git ~/MCP_Servers
```

---

## Konfiguracija za OpenCode

### 1. Ubuntu Server MCP

```json
{
  "mcpServers": {
    "ubuntu-server": {
      "command": "node",
      "args": ["/home/dju/MCP_Servers/servers/javascript/ubuntu-server/index.js"]
    }
  }
}
```

### 2. AI Learning MCP

```json
{
  "mcpServers": {
    "ai-learning": {
      "command": "python",
      "args": ["-m", "ai_learning_mcp"],
      "cwd": "/home/dju/MCP_Servers/servers/python/ai-learning"
    }
  }
}
```

### 3. HP OneView MCP

```json
{
  "mcpServers": {
    "hponeview": {
      "command": "python",
      "args": ["/home/dju/MCP_Servers/servers/python/hponeview/main.py"],
      "env": {
        "HPE_OV_HOST": "your-ov-host",
        "HPE_OV_USER": "your-user",
        "HPE_OV_PASSWORD": "your-password"
      }
    }
  }
}
```

---

## Instalacija Dependencies

### JavaScript Serveri
```bash
cd ~/MCP_Servers/servers/javascript/ubuntu-server
npm install
```

### Python Serveri
```bash
# AI Learning
cd ~/MCP_Servers/servers/python/ai-learning
pip install -e .

# HP OneView
cd ~/MCP_Servers/servers/python/hponeview
pip install -r requirements.txt
```

---

## Testiranje Servera

### Ubuntu Server
```bash
cd ~/MCP_Servers/servers/javascript/ubuntu-server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node index.js
```

### AI Learning
```bash
cd ~/MCP_Servers/servers/python/ai-learning
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python -m ai_learning_mcp
```

---

## Dostupni Tool-ovi

### Ubuntu Server
| Tool | Opis |
|------|-------|
| proveri_sistem | CPU, RAM, disk usage |
| proveri_cpu | Top procesi |
| proveri_mrezu | Mrežne konekcije |
| proveri_disk | Disk informacije |
| proveri_procese | Aktivni procesi |

### AI Learning
| Tool | Opis |
|------|-------|
| health_check | Health status |
| (više tool-ova u razvoju) |

---

## Eksterni MCP Serveri

### Automatski učitani
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "mcp-server-brave-search"]
    },
    "docker": {
      "command": "docker-mcp"
    },
    "firecrawl": {
      "command": "firecrawl-mcp"
    },
    "playwright": {
      "command": "playwright-mcp"
    }
  }
}
```

---

## Troubleshooting

### Server se ne pokreće
1. Proveri dependencies: `npm install` ili `pip install`
2. Proveri putanju u config
3. Proveri logove: `journalctl -u opencode`

### Tool-ovi se ne vide
1. Restart OpenCode
2. Proveri MCP config
3. Testiraj server direktno
