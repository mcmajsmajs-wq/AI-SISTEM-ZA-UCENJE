#!/bin/bash
# MCP Klijent - Docker verzija
# Ne zahteva instalaciju MCP paketa lokalno

set -e

MCP_SERVER="${1:-brave-search}"
COMMAND="${2:-list}"

show_help() {
    cat << EOF
Usage: ./docker-mcp-client.sh <server> <command>

Serveri:
  brave-search        Brave Search MCP
  sequential-thinking Sequential Thinking MCP
  firecrawl           Firecrawl Web Scraper
  docker              Docker MCP
  github              GitHub MCP

Komande:
  list                Lista dostupne alate
  tools               Lista dostupne alate (alias)
  prompts             Lista dostupne prompt-ove

Primeri:
  ./docker-mcp-client.sh brave-search list
  ./docker-mcp-client.sh sequential-thinking list
  ./docker-mcp-client.sh firecrawl list

EOF
}

case "$MCP_SERVER" in
    brave-search)
        IMAGE="@modelcontextprotocol/server-brave-search"
        CMD="npx -y ${IMAGE}"
        ;;
    sequential-thinking)
        IMAGE="@modelcontextprotocol/server-sequential-thinking"
        CMD="npx -y ${IMAGE}"
        ;;
    firecrawl)
        IMAGE="firecrawl-mcp"
        CMD="npx -y ${IMAGE}"
        ;;
    docker)
        IMAGE="mcp-docker-server"
        CMD="npx -y ${IMAGE}"
        ;;
    github)
        IMAGE="@modelcontextprotocol/server-github"
        CMD="npx -y ${IMAGE}"
        ;;
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        echo "❌ Nepoznat server: $MCP_SERVER"
        show_help
        exit 1
        ;;
esac

echo "🔌 Povezivanje sa MCP serverom: $MCP_SERVER"
echo ""

if [ "$COMMAND" = "list" ] || [ "$COMMAND" = "tools" ]; then
    echo "📋 Dohvatanje lista alata..."
    docker run --rm \
        --network none \
        -i \
        ghcr.io/modelcontextprotocol/python-sdk:latest \
        python -c "
import json
import sys
sys.path.insert(0, '/sdk')
from mcp.client.stdio import stdio_client
from mcp import ClientSession

async def main():
    transport = stdio_client({'command': 'npx', 'args': ['-y', '$IMAGE']})
    async with transport as (read, write):
        session = ClientSession(read, write)
        await session.initialize()
        result = await session.list_tools()
        print(json.dumps(result.dict(), indent=2))

asyncio.run(main())
" 2>/dev/null || echo "Docker/SDK nije dostupan. Koristite Node.js verziju."
fi
