# -*- coding: utf-8 -*-
"""
Quiz MCP Tools - FAZA 7
Alati za upravljanje kvizovima kroz MCP.
"""

from mcp.types import Tool


def get_quiz_tools() -> list[Tool]:
    """Vraca listu Quiz MCP alata."""
    return [
        Tool(
            name="quiz_create",
            description="Create a new quiz from document chunks with AI-generated questions",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "integer",
                        "description": "ID of the document to generate quiz from",
                    },
                    "title": {"type": "string", "description": "Title for the quiz"},
                    "num_questions": {
                        "type": "integer",
                        "description": "Number of questions to generate (default: 10)",
                        "default": 10,
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "subject_area": {
                        "type": "string",
                        "description": "Subject area (math, physics, chemistry, etc.)",
                    },
                    "provider": {
                        "type": "string",
                        "description": "AI provider to use",
                        "enum": [
                            "openai",
                            "claude",
                            "gemini",
                            "ollama",
                            "groq",
                            "mistral",
                        ],
                        "default": "openai",
                    },
                },
                "required": ["document_id", "title"],
            },
        ),
        Tool(
            name="quiz_list",
            description="List user's quizzes with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "integer",
                        "description": "User ID (optional, uses current user if not provided)",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status",
                        "enum": ["pending", "processing", "completed", "failed", "all"],
                        "default": "all",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of quizzes to return",
                        "default": 20,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="quiz_get",
            description="Get quiz details including all questions and answers",
            inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {
                        "type": "integer",
                        "description": "ID of the quiz to retrieve",
                    },
                    "include_answers": {
                        "type": "boolean",
                        "description": "Include correct answers in response",
                        "default": False,
                    },
                },
                "required": ["quiz_id"],
            },
        ),
        Tool(
            name="quiz_submit_attempt",
            description="Submit answers for a quiz attempt and get results",
            inputSchema={
                "type": "object",
                "properties": {
                    "quiz_id": {
                        "type": "integer",
                        "description": "ID of the quiz to attempt",
                    },
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "question_id": {"type": "integer"},
                                "answer": {"type": "string"},
                            },
                        },
                        "description": "Array of answers in format [{question_id: int, answer: str}, ...]",
                    },
                },
                "required": ["quiz_id", "answers"],
            },
        ),
        Tool(
            name="quiz_get_providers",
            description="Get list of available AI providers for quiz generation",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]
