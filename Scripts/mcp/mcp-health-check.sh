#!/bin/bash
echo "--- MCP & AI Process Monitor ---"
# Tražimo procese povezane sa opencode i mcp-om
ps aux | grep -E 'opencode|mcp|runtime' | grep -v grep | awk '{print "PID: "$2" | CPU: "$3"% | MEM: "$4"% | CMD: "$11}'
echo "--------------------------------"
echo "Ukupno zauzeće diska u WSL-u:"
df -h / | grep /
