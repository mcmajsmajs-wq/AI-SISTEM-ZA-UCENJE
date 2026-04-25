#!/bin/bash
# Web Scraper za seoska imanja u okolini Beograda
# Koristi curl i grep umesto Playwright-a

echo "=========================================="
echo "WEB SCRAPER - Seoska imanja Beograd"
echo "Cilj: 15.000 - 20.000 EUR"
echo "=========================================="
echo ""

OUTPUT_FILE="/home/dju/moji projekti/Web SCreper/rezultati_oglasi.txt"

# Funkcija za čišćenje HTML-a
clean_html() {
    sed 's/<[^>]*>//g' | sed 's/&nbsp;/ /g' | sed 's/&quot;/"/g' | sed 's/&amp;/\&/g'
}

# Funkcija za ekstrakciju cene
extract_price() {
    grep -oE '[0-9]+[.,]?[0-9]*' | head -1 | tr -d '.,'
}

# Funkcija za proveru cene (15.000 - 20.000)
check_price_range() {
    local price=$1
    if [[ $price =~ ^[0-9]+$ ]]; then
        if [ "$price" -ge 15000 ] && [ "$price" -le 20000 ]; then
            return 0
        fi
    fi
    return 1
}

echo "Pretražujem sajtove..."
echo ""

# Inicijalizuje izlazni fajl
echo "Rezultati pretrage seoskih imanja" > "$OUTPUT_FILE"
echo "Datum: $(date)" >> "$OUTPUT_FILE"
echo "Kriterijumi: 15.000 - 20.000 EUR, okolina Beograda" >> "$OUTPUT_FILE"
echo "============================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Brojač oglasa
count=0

# 1. Pretražuje Nekretnine.rs
echo "1. Pretražujem nekretnine.rs..."
curl -s -L "https://www.nekretnine.rs/stambeni-objekti/kuce/beograd/cena/15000_20000/" \
    -H "User-Agent: Mozilla/5.0" \
    --connect-timeout 10 2>/dev/null | \
    grep -oE '<a[^>]*href="[^"]*"[^>]*>[^<]*</a>' | \
    while read -r line; do
        link=$(echo "$line" | grep -oE 'href="[^"]*"' | sed 's/href="//;s/"$//')
        title=$(echo "$line" | clean_html)
        
        if [[ "$link" == *"/oglasi"* ]] && [ ${#title} -gt 10 ]; then
            # Proverava da li je link validan
            if [[ "$link" != http* ]]; then
                link="https://www.nekretnine.rs$link"
            fi
            
            ((count++))
            echo "$count. $title" >> "$OUTPUT_FILE"
            echo "   Link: $link" >> "$OUTPUT_FILE"
            echo "   Izvor: nekretnine.rs" >> "$OUTPUT_FILE"
            echo "------------------------------------------------------------" >> "$OUTPUT_FILE"
            echo ""
        fi
done

# 2. Pretražuje OLX.rs
echo "2. Pretražujem OLX.rs..."
curl -s -L "https://www.olx.rs/d/nedviznosti/prodazha/kukhi/beograd/" \
    -H "User-Agent: Mozilla/5.0" \
    --connect-timeout 10 2>/dev/null | \
    grep -oE '<a[^>]*href="[^"]*"[^>]*>[^<]*</a>' | \
    head -50 | \
    while read -r line; do
        link=$(echo "$line" | grep -oE 'href="[^"]*"' | sed 's/href="//;s/"$//')
        title=$(echo "$line" | clean_html)
        
        if [[ "$link" == *"/d/ogl"* ]] && [ ${#title} -gt 5 ]; then
            if [[ "$link" != http* ]]; then
                link="https://www.olx.rs$link"
            fi
            
            ((count++))
            echo "$count. $title" >> "$OUTPUT_FILE"
            echo "   Link: $link" >> "$OUTPUT_FILE"
            echo "   Izvor: olx.rs" >> "$OUTPUT_FILE"
            echo "------------------------------------------------------------" >> "$OUTPUT_FILE"
            echo ""
        fi
done

# 3. Pretražuje Halooglasi
echo "3. Pretražujem Halooglasi..."
curl -s -L "https://www.halooglasi.com/nedviznosti/prodaja-kukha/beograd" \
    -H "User-Agent: Mozilla/5.0" \
    --connect-timeout 10 2>/dev/null | \
    grep -oE '<a[^>]*href="[^"]*"[^>]*>[^<]*</a>' | \
    head -50 | \
    while read -r line; do
        link=$(echo "$line" | grep -oE 'href="[^"]*"' | sed 's/href="//;s/"$//')
        title=$(echo "$line" | clean_html)
        
        if [[ "$link" == *"/oglasi"* ]] && [ ${#title} -gt 10 ]; then
            if [[ "$link" != http* ]]; then
                link="https://www.halooglasi.com$link"
            fi
            
            ((count++))
            echo "$count. $title" >> "$OUTPUT_FILE"
            echo "   Link: $link" >> "$OUTPUT_FILE"
            echo "   Izvor: halooglasi.com" >> "$OUTPUT_FILE"
            echo "------------------------------------------------------------" >> "$OUTPUT_FILE"
            echo ""
        fi
done

# Dodaje napomenu na kraj
echo "" >> "$OUTPUT_FILE"
echo "============================================================" >> "$OUTPUT_FILE"
echo "NAPOMENA: Ovo su rezultati automatske pretrage." >> "$OUTPUT_FILE"
echo "Preporučuje se ručna provera svakog oglasa." >> "$OUTPUT_FILE"
echo "Cene i lokacije treba dodatno verifikovati." >> "$OUTPUT_FILE"
echo "============================================================" >> "$OUTPUT_FILE"

echo ""
echo "=========================================="
echo "PRETRAGA ZAVRŠENA!"
echo "Ukupno pronađeno: $count oglasa"
echo "Rezultati sačuvani u:"
echo "$OUTPUT_FILE"
echo "=========================================="
