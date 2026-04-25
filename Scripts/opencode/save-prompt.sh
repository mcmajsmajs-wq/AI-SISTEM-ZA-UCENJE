#!/bin/bash
# save-prompt.sh - Sačuvaj trenutni razgovor
# Usage: ~/Scripts/opencode/save-prompt.sh [kategorija] [naslov]

set -e

KATEGORIJA="${1:-}"
NASLOV="${2:-}"
DANAS_DIR="$HOME/Prompts/danas"
ARHIVA_DIR="$HOME/Prompts/arhiva"
KATEGORIJE_DIR="$HOME/Prompts/kategorije"
DATUM=$(date +%Y-%m-%d)
VREME=$(date +%H-%M)
IME_FAJLA="${DATUM}_${VREME}.md"

# Pronađi session fajl ako postoji
SESSION_FILE=""
for f in /tmp/opencode-session*.md /tmp/opencode*.md; do
    if [ -f "$f" ]; then
        SESSION_FILE="$f"
        break
    fi
done

# Ako nema session fajla, pitaj korisnika
if [ -z "$SESSION_FILE" ]; then
    echo "Nema aktuelnog session fajla u /tmp/"
    echo "Kreiram prazan template..."
    
    # Kreiraj template
    SADRZAJ="# OpenCode Session - ${DATUM} ${VREME}

## Naslov
${NASLOV:-Nenaslovljen razgovor}

## Kategorija
${KATEGORIJA:-neodređeno}

## Datum
${DATUM} ${VREME}

## Rezime

<!-- Unesi rezime razgovora ovde -->

## Ključne tačke

- 

## Akcije za sledeći put

- 

---

*Automatski generisano: $(date '+%Y-%m-%d %H:%M:%S')*
"
else
    SADRZAJ=$(cat "$SESSION_FILE")
fi

# Sačuvaj u danas/
mkdir -p "$DANAS_DIR"
echo "$SADRZAJ" > "$DANAS_DIR/$IME_FAJLA"
echo "✓ Sačuvano u: $DANAS_DIR/$IME_FAJLA"

# Ako je data kategorija, sačuvaj i tamo
if [ -n "$KATEGORIJA" ]; then
    if [ -d "$KATEGORIJE_DIR/$KATEGORIJA" ]; then
        echo "$SADRZAJ" > "$KATEGORIJE_DIR/$KATEGORIJA/$IME_FAJLA"
        echo "✓ Kopirano u: $KATEGORIJE_DIR/$KATEGORIJA/$IME_FAJLA"
    else
        echo "⚠ Nepoznata kategorija: $KATEGORIJA"
        echo "  Dostupne: $(ls $KATEGORIJE_DIR)"
    fi
fi

echo ""
echo "Gotovo!"
