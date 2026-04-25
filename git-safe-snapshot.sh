#!/bin/bash
MAX_SIZE=52428800 # 50MB u bajtovima

echo "Skeniram fajlove pre snapshota..."
# Pronalazi velike fajlove koji nisu u .gitignore
LARGE_FILES=$(find . -type f -size +50M -not -path '*/.*')

if [ ! -z "$LARGE_FILES" ]; then
    echo "⚠️ UPOZORENJE: Pronađeni su preveliki fajlovi:"
    echo "$LARGE_FILES"
    echo "Ovi fajlovi NEĆE biti dodati da se ne bi ponovio problem sa diskom."
fi

# Dodaje samo fajlove manje od 50MB
find . -type f -size -50M -not -path '*/.*' -exec git add {} +
git commit -m "Safe snapshot: $(date)"
echo "✅ Siguran snapshot završen."
