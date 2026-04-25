#!/bin/bash
echo "Čistim razvojno okruženje..."

# Čišćenje npm keša
npm cache clean --force 2>/dev/null

# Čišćenje starih Python bytecode fajlova
find . -type d -name "__pycache__" -exec rm -rf {} +

# Čišćenje Bun keša (pošto ga imaš na sistemu)
bun pm cache rm

# Čišćenje neiskorišćenih paketa
sudo apt-get autoremove -y && sudo apt-get autoclean

echo "✅ Sistem je osvežen."
