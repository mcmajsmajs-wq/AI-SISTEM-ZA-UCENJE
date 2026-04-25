# ================================================================================
# DOCKERFILE - AI LEARNING SYSTEM (DEVELOPMENT)
# ================================================================================
# Python 3.11 slim image sa svim dependency-jima
# ================================================================================

FROM python:3.11-slim

# ================================================================================
# LABELS
# ================================================================================
LABEL maintainer="AI Learning System Team"
LABEL version="1.0.0"
LABEL description="AI Learning System - Backend API"

# ================================================================================
# SYSTEM DEPENDENCIES
# ================================================================================
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Build dependencies
    gcc \
    g++ \
    libc-dev \
    libpq-dev \
    # PDF processing
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    # Tesseract OCR
    tesseract-ocr \
    tesseract-ocr-srp \
    tesseract-ocr-srp-latn \
    tesseract-ocr-eng \
    # Utils
    curl \
    && rm -rf /var/lib/apt/lists/*

# ================================================================================
# PYTHON ENVIRONMENT
# ================================================================================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

# ================================================================================
# WORK DIRECTORY
# ================================================================================
WORKDIR /app

# ================================================================================
# INSTALL PYTHON DEPENDENCIES
# ================================================================================
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ================================================================================
# COPY APPLICATION CODE
# ================================================================================
COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .

# ================================================================================
# CREATE LOGS DIRECTORY
# ================================================================================
RUN mkdir -p /app/logs && \
    chmod 755 /app/logs

# ================================================================================
# CREATE NON-ROOT USER
# ================================================================================
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# ================================================================================
# EXPOSE PORT
# ================================================================================
EXPOSE 8000

# ================================================================================
# HEALTH CHECK
# ================================================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ================================================================================
# START COMMAND
# ================================================================================
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
