#!/bin/bash
SESSION_DIR="$HOME/.config/opencode/sessions"
if [ -d "$SESSION_DIR" ]; then
    mkdir -p "$SESSION_DIR/archive"
    for file in "$SESSION_DIR"/*.log; do
        if [ -f "$file" ]; then
            tail -n 100 "$file" > "${file}.tmp" && mv "${file}.tmp" "$file"
            echo "Kompresovan: $file"
        fi
    done
else
    echo "Nema aktivnih sesija za kompresiju."
fi
