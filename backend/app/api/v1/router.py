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

from app.api.endpoints import auth
from app.api.endpoints import users
from app.api.endpoints import files
from app.api.endpoints import documents
from app.api.endpoints import health
from app.api.endpoints import quizzes
from app.api.endpoints import study_plan
from app.api.endpoints import analytics
from app.api.endpoints import knowledge
from app.api.endpoints import intelligence_test
from app.api.endpoints import chat
from app.api.endpoints import providers
from app.api.endpoints import gamification

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
    quizzes.router,
    prefix="/quizzes",
    tags=["Quizzes"]
)

# Study Plan
api_router.include_router(
    study_plan.router,
    prefix="/study-plan",
    tags=["Study Plan"]
)

# Analytics
api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["Analytics"]
)

# Knowledge Base (RAG)
api_router.include_router(
    knowledge.router,
    prefix="/knowledge",
    tags=["Knowledge"]
)

# Intelligence Test
api_router.include_router(
    intelligence_test.router,
    prefix="/intelligence-test",
    tags=["Intelligence Test"]
)

# AI Chat
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["AI Chat"]
)

# Providery Health Check
api_router.include_router(
    providers.router,
    prefix="/providers",
    tags=["Providers"]
)

# Gamification
api_router.include_router(
    gamification.router,
    prefix="/gamification",
    tags=["Gamification"]
)

# TODO: Dodati ostale endpoint-e kada se implementiraju:
# - calendar
# - analytics
# - search
# - admin
