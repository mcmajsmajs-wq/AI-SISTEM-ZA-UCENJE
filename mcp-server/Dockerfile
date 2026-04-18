# ================================================================================
# MCP SERVER DOCKERFILE
# AI Learning System - MCP Server Container
# Verzija: 1.0.0
# ================================================================================

FROM python:3.11-slim

# ================================================================================
# METADATA
# ================================================================================
LABEL maintainer="AI Learning System" \
      version="1.0.0" \
      description="MCP Server for AI Learning System"

# ================================================================================
# ENVIRONMENT SETUP
# ================================================================================
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # MCP ce koristiti backend API preko Docker network-a
    API_BASE_URL=http://ai-learning-app:8000

WORKDIR /app

# ================================================================================
# INSTALL SYSTEM DEPENDENCIES
# ================================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ================================================================================
# INSTALL PYTHON DEPENDENCIES
# ================================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ================================================================================
# COPY MCP SERVER SOURCE
# ================================================================================
COPY src/ ./src/
COPY pyproject.toml .

# ================================================================================
# CREATE PYTHON PATH
# ================================================================================
ENV PYTHONPATH=/app/src

# ================================================================================
# HEALTHCHECK - Disabled for MCP (stdio mode)
# ================================================================================
# MCP koristi stdio za komunikaciju - healthcheck nije potreban

# ================================================================================
# ENTRYPOINT
# ================================================================================
# MCP koristi stdio za komunikaciju sa AI alatima
CMD ["tail", "-f", "/dev/null"]