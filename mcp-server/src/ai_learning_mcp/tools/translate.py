# -*- coding: utf-8 -*-
"""
Translation MCP Tools - FAZA 7
Alati za prevodjenje tekstova kroz MCP.
"""

from mcp.types import Tool


def get_translate_tools() -> list[Tool]:
    """Vraca listu Translation MCP alata."""
    return [
        Tool(
            name="translate_text",
            description="Translate text between languages using AI",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to translate"
                    },
                    "source_language": {
                        "type": "string",
                        "description": "Source language code or name (e.g., 'en', 'sr', 'de')"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language code or name (e.g., 'en', 'sr', 'de')"
                    },
                    "provider": {
                        "type": "string",
                        "description": "AI provider to use",
                        "enum": ["openai", "claude", "gemini", "deepseek", "ollama"],
                        "default": "openai"
                    },
                    "user_api_key": {
                        "type": "string",
                        "description": "User's API key for the provider (optional)"
                    }
                },
                "required": ["text", "source_language", "target_language"]
            }
        ),
        Tool(
            name="translate_batch",
            description="Translate multiple texts at once",
            inputSchema={
                "type": "object",
                "properties": {
                    "texts": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Array of texts to translate"
                    },
                    "source_language": {
                        "type": "string",
                        "description": "Source language code"
                    },
                    "target_language": {
                        "type": "string",
                        "description": "Target language code"
                    },
                    "provider": {
                        "type": "string",
                        "description": "AI provider to use",
                        "enum": ["openai", "claude", "gemini", "deepseek", "ollama"],
                        "default": "openai"
                    }
                },
                "required": ["texts", "source_language", "target_language"]
            }
        ),
        Tool(
            name="translate_supported_languages",
            description="Get list of supported languages for translation",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
    ]