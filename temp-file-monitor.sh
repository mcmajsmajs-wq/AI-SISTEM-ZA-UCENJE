#!/bin/bash
# Lokacija privremenih fajlova tvog OpenCode AI-a ili sistema
TARGET_DIR="/tmp"
DAYS=7

echo "Uklanjam privremene fajlove starije od $DAYS dana iz $TARGET_DIR..."

# Pronalazi i briše fajlove (-mtime +7 znači starije od 7 dana)
find $TARGET_DIR -maxdepth 1 -type f -mtime +$DAYS -exec rm -f {} \;

echo "✅ Čišćenje završeno."
