#!/bin/bash
# Isključujemo nepotrebne ispise koji kvare MCP
export DOTNET_CLI_TELEMETRY_OPTOUT=1
export DOTNET_NOLOGO=1

# Pokrećemo Windows dotnet direktno iz Linuxa
/mnt/c/Program\ Files/dotnet/dotnet.exe \
  C:\\Users\\admin\\Documents\\KucniGit\\MCP-Dotnet\\awesome-copilot\\src\\McpSamples.AwesomeCopilot.HybridApp\\bin\\Release\\net9.0\\McpSamples.AwesomeCopilot.HybridApp.dll

