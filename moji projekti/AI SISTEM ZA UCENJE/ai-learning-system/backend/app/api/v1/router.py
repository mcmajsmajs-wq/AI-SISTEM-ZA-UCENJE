# -*- coding: utf-8 -*-
"""
================================================================================
API ROUTER
================================================================================
Centralni router koji spaja sve endpoint-e.

Verzija: 1.0.0
================================================================================
"""

from fastapi import APIRouter

from app.api.endpoints import auth, users, files, documents, health, quiz, pdf_generator, calendar, backup, analytics

# ================================================================================
# GLAVNI API ROUTER
# ================================================================================
api_router = APIRouter()

# ================================================================================
# REGISTRACIJA ENDPOINTA
# ================================================================================

# Health check (nema prefix jer su root level)
api_router.include_router(health.router, tags=["Health"])

# Authentication
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"]
)

# Users
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

# Files
api_router.include_router(
    files.router,
    prefix="/files",
    tags=["Files"]
)

# Documents
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["Documents"]
)

# Quizzes
api_router.include_router(
    quiz.router,
    prefix="/quizzes",
    tags=["Quizzes"]
)

# PDF Generator
api_router.include_router(
    pdf_generator.router,
    prefix="/export",
    tags=["PDF Export"]
)

# Calendar
api_router.include_router(
    calendar.router,
    prefix="/calendar",
    tags=["Calendar"]
)

# Backup
api_router.include_router(
    backup.router,
    prefix="/backup",
    tags=["Backup"]
)

# Analytics
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# TODO: Dodati ostale endpoint-e kada se implementiraju:
# - calendar
# - analytics
# - search
# - admin
