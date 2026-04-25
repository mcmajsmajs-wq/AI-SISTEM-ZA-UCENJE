# MCP Klijenti

Ovi klijenti omogucavaju povezivanje sa MCP serverima na razliche nachine.

## Struktura

```
mcp-clients/
├── basic-client.js        # Jednostavni primer
├── client-manager.js      # Manager za vise servera
├── cli-client.js          # CLI alat (preporucheno)
├── rest-api-server.js     # REST API wrapper
├── python-client.py       # Python verzija (zahteva pip install mcp)
└── docker-mcp-client.sh   # Docker verzija
```

## Brzi start

### 1. CLI Klijent (Najjednostavniji)

```bash
cd ~/MCP_Servers/clients

# Lista alata za server
node cli-client.js brave-search --list

# Pozovi alat
node cli-client.js brave-search brave-web-search "MCP protocol"

# Pozovi sequential thinking
node cli-client.js sequential-thinking sequentialthinking "Kako da optimizujem kod?"
```

### 2. Programmatic API

```javascript
const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function main() {
  const transport = new StdioClientTransport({
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-brave-search'],
    env: { ...process.env, BRAVE_API_KEY: 'vas_kljuc' }
  });

  const client = new Client({ name: 'my-client', version: '1.0.0' });
  await client.connect(transport);

  // Lista alata
  const tools = await client.listTools();
  console.log(tools);

  // Pozovi alat
  const result = await client.callTool({
    name: 'brave-web-search',
    arguments: { query: 'test' }
  });

  await client.close();
}
```

### 3. REST API Server

```bash
# Pokreni server
node rest-api-server.js

# Lista dostupnih servera
curl http://localhost:3000/servers

# Lista alata za server
curl http://localhost:3000/servers/brave-search/tools

# Pozovi alat
curl -X POST http://localhost:3000/servers/brave-search/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "brave-web-search", "arguments": {"query": "MCP"}}'
```

### 4. Python Klijent

```bash
# Instalacija
pip install mcp

# Pokretanje
python python-client-simple.py
```

## Dostupni serveri u CLI klijentu

| Server | Opis | Potrebni tokensi |
|--------|------|------------------|
| brave-search | Web pretraga | BRAVE_API_KEY |
| sequential-thinking | Strukturalno razmisljanje | - |
| firecrawl | Web scraping | FIRECRAWL_API_KEY |
| docker | Docker upravljanje | - |
| github | GitHub integracija | GITHUB_PERSONAL_ACCESS_TOKEN |
| gmail | Gmail integracija | GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET |

## Environment Variables

Postavite pre pokretanja:

```bash
export BRAVE_API_KEY="vas_brave_kljuc"
export FIRECRAWL_API_KEY="vas_firecrawl_kljuc"
export GITHUB_PERSONAL_ACCESS_TOKEN="vas_github_token"
```
