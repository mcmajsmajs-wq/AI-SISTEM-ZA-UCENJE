# MCP Servers Repository

Centralizovano skladište svih MCP servera.

## Struktura

```
/home/dju/MCP_Servers/
├── README.md                     # Ovaj fajl
├── servers/                      # Server implementacije
│   ├── javascript/
│   │   └── ubuntu-server/     # Sistemski monitoring (Node.js)
│   │       ├── index.js
│   │       ├── package.json
│   │       └── node_modules/
│   ├── python/
│   │   ├── ai-learning/        # AI Learning platform
│   │   │   ├── src/
│   │   │   └── README.md
│   │   └── hponeview/         # HP OneView integracija
│   │       ├── main.py
│   │       ├── server.py
│   │       └── docs/
│   └── dotnet/
│       └── samples/            # .NET primeri
├── clients/                     # MCP Klijenti
│   ├── cli-client.js           # CLI interfejs
│   ├── client-manager.js       # Upravljanje klijentima
│   └── python-client.py        # Python klijent
├── config/                      # Konfiguracije
│   └── opencode-mcp-config.json  # OpenCode MCP settings
├── docs/                       # Dokumentacija
│   └── OPENCODE_INTEGRATION.md
└── scripts/                    # Skripte
    └── start-servers.sh       # Startup skripta
```

## Servers

| Server | Jezik | Putanja | Opis |
|--------|-------|--------|-------|
| ubuntu-server | JavaScript | `servers/javascript/ubuntu-server` | CPU, RAM, disk, mreža monitoring |
| ai-learning | Python | `servers/python/ai-learning` | AI Learning platform |
| hponeview | Python | `servers/python/hponeview` | HP OneView integracija |
| samples | C# | `servers/dotnet/samples` | .NET primeri |

## Quick Start

### Ubuntu Server
```bash
cd servers/javascript/ubuntu-server
npm install
node index.js
```

### AI Learning
```bash
cd servers/python/ai-learning
pip install -e .
python -m ai_learning_mcp
```

### HP OneView
```bash
cd servers/python/hponeview
pip install -r requirements.txt
python main.py
```

## Upravljanje Serverima

```bash
./scripts/start-servers.sh start    # Start all
./scripts/start-servers.sh stop     # Stop all
./scripts/start-servers.sh restart  # Restart all
./scripts/start-servers.sh status   # Check status
```

## OpenCode Konfiguracija

Pogledaj: [docs/OPENCODE_INTEGRATION.md](./docs/OPENCODE_INTEGRATION.md)

## Dokumentacija

- [OpenCode Integracija](./docs/OPENCODE_INTEGRATION.md)
- [Ubuntu Server](./servers/javascript/ubuntu-server/README.md)
- [AI Learning](./servers/python/ai-learning/README.md)

## Skills

Za OpenCode koristi skill `mcp-servers`:
```
/skill mcp-servers
```
