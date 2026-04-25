#!/bin/bash
if [ -z "$1" ]; then
    echo "Upotreba: ./auto-mcp-installer.sh <naziv-paketa>"
    exit 1
fi

PACKAGE=$1
echo "Instaliram MCP alat: $PACKAGE..."

cd /home/dju/.config/opencode
bun add $PACKAGE  # Koristimo bun jer smo ga videli u tvom folderu

echo "Dopisujem alat u opencode.json..."
# Koristi jq za editovanje JSON-a (instaliraj sa: sudo apt install jq)
jq ".mcp.runtime.command += [\"$PACKAGE\"]" opencode.json > tmp.json && mv tmp.json opencode.json

echo "✅ Alat $PACKAGE je instaliran i dodat u runtime."
