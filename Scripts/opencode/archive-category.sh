#!/bin/bash
# archive-category.sh - Arhiviraj celu kategoriju starih razgovora
# Usage: ~/Scripts/opencode/archive-category.sh [kategorija] [starije_od_dana]

set -e

KATEGORIJA="${1:-}"
DANA="${2:-7}"

if [ -z "$KATEGORIJA" ]; then
    echo "Korišćenje: $0 [kategorija] [starije_od_dana]"
    echo ""
    echo "Dostupne kategorije:"
    ls "$HOME/Prompts/kategorije/"
    exit 1
fi

KAT_DIR="$HOME/Prompts/kategorije/$KATEGORIJA"
ARHIVA_DIR="$HOME/Prompts/arhiva"
GODINA=$(date +%Y)
MESEC=$(date +%m)

if [ ! -d "$KAT_DIR" ]; then
    echo "Nepoznata kategorija: $KATEGORIJA"
    exit 1
fi

mkdir -p "$ARHIVA_DIR/$GODINA/$MESEC"

# Pronađi stare fajlove
DATUM_OD=$(date +%Y-%m-%d --date="$DANA days ago")

BROJ=0
for FAJL in "$KAT_DIR"/*.md; do
    [ -f "$FAJL" ] || continue
    
    # Izvuci datum iz imena fajla
    IME=$(basename "$FAJL")
    FAJL_DATUM=$(echo "$IME" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')
    
    if [ -n "$FAJL_DATUM" ] && [[ "$FAJL_DATUM" < "$DATUM_OD" ]]; then
        mv "$FAJL" "$ARHIVA_DIR/$GODINA/$MESEC/"
        echo "✓ Arhiviran: $FAJL"
        ((BROJ++))
    fi
done

echo ""
echo "Ukupno arhivirano: $BROJ fajlova"
