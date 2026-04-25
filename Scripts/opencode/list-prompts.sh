#!/bin/bash
# list-prompts.sh - Lista razgovora
# Usage: ~/Scripts/opencode/list-prompts.sh [filter]

FILTER="${1:-}"
DANAS_DIR="$HOME/Prompts/danas"
KAT_DIR="$HOME/Prompts/kategorije"
ARHIVA_DIR="$HOME/Prompts/arhiva"

echo "═══════════════════════════════════════════════════════════"
echo "           📁 OpenCode Prompt Arhiva"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Današnji
echo "📅 DANAS ($HOME/Prompts/danas/):"
if [ "$(ls -A $DANAS_DIR 2>/dev/null)" ]; then
    ls -la "$DANAS_DIR" | tail -n +4 | awk '{print "   " $6, $7, $8, $9}'
else
    echo "   (prazno)"
fi
echo ""

# Kategorije
echo "📂 PO KATEGORIJAMA:"
for KAT in "$KAT_DIR"/*; do
    [ -d "$KAT" ] || continue
    IME=$(basename "$KAT")
    BROJ=$(ls "$KAT"/*.md 2>/dev/null | wc -l)
    echo "   $IME: $BROJ fajlova"
done
echo ""

# Arhiva po mesecima
echo "📦 ARHIVA:"
for GOD in "$ARHIVA_DIR"/*; do
    [ -d "$GOD" ] || continue
    GODINA=$(basename "$GOD")
    for MES in "$GOD"/*; do
        [ -d "$MES" ] || continue
        IME=$(basename "$MES")
        BROJ=$(ls "$MES"/*.md 2>/dev/null | wc -l)
        echo "   $GODINA/$IME: $BROJ fajlova"
    done
done

echo ""
echo "═══════════════════════════════════════════════════════════"
