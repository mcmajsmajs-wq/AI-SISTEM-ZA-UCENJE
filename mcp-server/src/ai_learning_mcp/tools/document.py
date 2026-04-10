# -*- coding: utf-8 -*-
"""
Document MCP Tools - FAZA 7
Alati za obradu dokumenata kroz MCP.
"""

from mcp.types import Tool


def get_document_tools() -> list[Tool]:
    """Vraca listu Document MCP alata."""
    return [
        Tool(
            name="document_process",
            description="Process PDF document and extract text chunks",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to PDF file or URL"
                    },
                    "user_id": {
                        "type": "integer",
                        "description": "User ID who owns the document"
                    },
                    "title": {
                        "type": "string",
                        "description": "Document title (optional)"
                    }
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="document_detect_skill",
            description="Detect document type and get appropriate skill template",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "integer",
                        "description": "ID of the document to analyze"
                    },
                    "sample_text": {
                        "type": "string",
                        "description": "Text sample to analyze (optional, uses chunks if not provided)"
                    }
                },
                "required": ["document_id"]
            }
        ),
        Tool(
            name="document_list",
            description="List user's documents with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User ID (optional)"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by processing status",
                        "enum": ["pending", "processing", "completed", "failed", "all"],
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of documents",
                        "default": 20
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="document_get_chunks",
            description="Get extracted text chunks from a document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "integer",
                        "description": "ID of the document"
                    },
                    "include_translation": {
                        "type": "boolean",
                        "description": "Include translations if available",
                        "default": False
                    }
                },
                "required": ["document_id"]
            }
        ),
    ]