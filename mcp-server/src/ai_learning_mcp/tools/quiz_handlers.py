# -*- coding: utf-8 -*-
"""
Quiz Tool Handlers - FAZA 7
Handlers za Quiz MCP alate.
"""

import os
from typing import Any, Dict, Optional
import httpx


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8010")


async def handle_quiz_create(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za quiz_create tool."""
    document_id = params["document_id"]
    title = params["title"]
    num_questions = params.get("num_questions", 10)
    subject_area = params.get("subject_area")
    provider = params.get("provider", "openai")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/quizzes/",
                headers=headers,
                json={
                    "document_id": document_id,
                    "title": title,
                    "num_questions": num_questions,
                    "subject_area": subject_area,
                    "provider": provider,
                },
            )
            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "status": "created",
                    "quiz_id": data.get("id"),
                    "message": f"Quiz '{title}' created successfully",
                }
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_quiz_list(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za quiz_list tool."""
    user_id = params.get("user_id")
    status = params.get("status", "all")
    limit = params.get("limit", 20)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            query_params = {"limit": limit}
            if status != "all":
                query_params["status"] = status

            response = await client.get(
                f"{API_BASE_URL}/api/v1/quizzes/", headers=headers, params=query_params
            )
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                return {"status": "ok", "quizzes": items, "total": len(items)}
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_quiz_get(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za quiz_get tool."""
    quiz_id = params["quiz_id"]
    include_answers = params.get("include_answers", False)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/quizzes/{quiz_id}", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                if not include_answers:
                    for q in data.get("questions", []):
                        q.pop("correct_answer", None)
                        q.pop("explanation", None)
                return {"status": "ok", "quiz": data}
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_quiz_submit_attempt(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za quiz_submit_attempt tool."""
    quiz_id = params["quiz_id"]
    answers = params["answers"]

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/quizzes/{quiz_id}/submit",
                headers=headers,
                json={"answers": answers},
            )
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "score": data.get("score"),
                    "correct_count": data.get("correct_count"),
                    "total_count": data.get("total_count"),
                    "results": data.get("results", []),
                }
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_quiz_get_providers() -> Dict[str, Any]:
    """Handler za quiz_get_providers tool."""
    providers = [
        {"name": "openai", "models": ["gpt-4o", "gpt-4o-mini"]},
        {"name": "claude", "models": ["claude-sonnet-4-20250514", "claude-3-opus"]},
        {"name": "gemini", "models": ["gemini-2.0-flash", "gemini-pro"]},
        {"name": "ollama", "models": ["llama3.1", "mistral"]},
        {"name": "groq", "models": ["llama-3.1-70b", "mixtral-8x7b"]},
        {"name": "mistral", "models": ["mistral-large", "codestral"]},
        {"name": "deepseek", "models": ["deepseek-chat"]},
    ]
    return {"status": "ok", "providers": providers}
