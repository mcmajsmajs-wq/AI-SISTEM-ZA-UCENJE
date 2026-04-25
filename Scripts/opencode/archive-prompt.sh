#!/bin/bash
# archive-prompt.sh - Arhiviraj stari razgovor
# Usage: ~/Scripts/opencode/archive-prompt.sh [datum] [kategorija]

set -e

DATUM="${1:-$(date +%Y-%m-%d --date='1 day ago')}"
KATEGORIJA="${2:-}"
DANAS_DIR="$HOME/Prompts/danas"
ARHIVA_DIR="$HOME/Prompts/arhiva"

# Izdvoji mesec i godinu
GODINA=$(echo $DATUM | cut -d'-' -f1)
MESEC=$(echo $DATUM | cut -d'-' -f2)

# Kreiraj arhivu ako ne postoji
mkdir -p "$ARHIVA_DIR/$GODINA/$MESEC"

# Pronađi fajl
FAJL=""
if [ -n "$KATEGORIJA" ] && [ -d "$HOME/Prompts/kategorije/$KATEGORIJA" ]; then
    FAVL=$(ls "$HOME/Prompts/kategorije/$KATEGORIJA"/${DATUM}_*.md 2>/dev/null | head -1)
fi

if [ -z "$FAJL" ]; then
    FAVL=$(ls "$DANAS_DIR"/${DATUM}_*.md 2>/dev/null | head -1)
fi

if [ -z "$FAJL" ]; then
    echo "Nije pronađen fajl za datum: $DATUM"
    echo "Dostupni fajlovi u danas/:"
    ls "$DANAS_DIR"/
    exit 1
fi

# Premesti u arhivu
mv "$FAJL" "$ARHIVA_DIR/$GODINA/$MESEC/"
echo "✓ Arhiviran: $FAJL -> $ARHIVA_DIR/$GODINA/$MESEC/"
