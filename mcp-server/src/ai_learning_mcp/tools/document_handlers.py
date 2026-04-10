# -*- coding: utf-8 -*-
"""
Document Tool Handlers - FAZA 7
Handlers za Document MCP alate.
"""

import os
from typing import Any, Dict, Optional
import httpx


API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


async def handle_document_process(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za document_process tool."""
    file_path = params["file_path"]
    user_id = params.get("user_id")
    title = params.get("title", file_path.split("/")[-1])

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/documents/",
                headers=headers,
                json={"file_path": file_path, "title": title, "user_id": user_id},
            )
            if response.status_code in (200, 201):
                data = response.json()
                return {
                    "status": "created",
                    "document_id": data.get("id"),
                    "message": f"Document '{title}' uploaded successfully",
                }
            return {
                "status": "error",
                "message": f"HTTP {response.status_code}: {response.text}",
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_document_detect_skill(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za document_detect_skill tool."""
    document_id = params["document_id"]
    sample_text = params.get("sample_text")

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if sample_text:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/documents/{document_id}/detect-skill",
                    headers=headers,
                    json={"text": sample_text},
                )
            else:
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/documents/{document_id}/skill",
                    headers=headers,
                )

            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "ok",
                    "category": data.get("category"),
                    "confidence": data.get("confidence"),
                    "keywords": data.get("keywords", []),
                }
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_document_list(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za document_list tool."""
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
                f"{API_BASE_URL}/api/v1/documents/",
                headers=headers,
                params=query_params,
            )
            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])
                return {"status": "ok", "documents": items, "total": len(items)}
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def handle_document_get_chunks(
    params: Dict[str, Any], token: Optional[str] = None
) -> Dict[str, Any]:
    """Handler za document_get_chunks tool."""
    document_id = params["document_id"]
    include_translation = params.get("include_translation", False)

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/documents/{document_id}/chunks",
                headers=headers,
                params={"include_translation": include_translation},
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    chunks = data.get("chunks", data.get("items", []))
                else:
                    chunks = data
                return {"status": "ok", "chunks": chunks, "count": len(chunks)}
            return {"status": "error", "message": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
