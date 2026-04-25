#!/bin/bash
DOMAIN="google.com"
echo "--- DNS Performance Tracker ---"
# Meri vreme odziva koristeći 'dig' alat
STATS=$(dig $DOMAIN | grep "Query time" | cut -d' ' -f4)

if [ -z "$STATS" ]; then
    echo "❌ DNS Error: Ne mogu da kontaktiram nameserver."
else
    echo "Vreme odziva za $DOMAIN: ${STATS}ms"
    if [ "$STATS" -gt 100 ]; then
        echo "⚠️ UPOZORENJE: DNS je spor. Proveri /etc/resolv.conf"
    else
        echo "✅ DNS brzina je optimalna."
    fi
fi
