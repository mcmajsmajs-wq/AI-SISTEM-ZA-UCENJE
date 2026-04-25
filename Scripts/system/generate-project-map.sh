#!/bin/bash
OUTPUT="project_map.md"
echo "# Project Structure - $(date)" > $OUTPUT
echo "## Directory Tree" >> $OUTPUT
echo '```' >> $OUTPUT
# Koristimo 'tree' ali ignorišemo teške foldere koje smo ranije pomenuli
tree -I 'node_modules|.git|.local|.cache' >> $OUTPUT
echo '```' >> $OUTPUT
echo "## Key Files Summary" >> $OUTPUT
find . -maxdepth 2 -not -path '*/.*' >> $OUTPUT
echo "Mapa projekta je generisana u $OUTPUT"
