# -*- coding: utf-8 -*-
"""
Skills MCP Tools - FAZA 7
Alati za detekciju tipa dokumenta i skill sisteme.
"""

from mcp.types import Tool


def get_skill_tools() -> list[Tool]:
    """Vraca listu Skills MCP alata."""
    return [
        Tool(
            name="skill_detect",
            description="Detect document type and get appropriate skill template from text",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text sample to analyze"
                    },
                    "threshold": {
                        "type": "integer",
                        "description": "Minimum confidence threshold (0-100)",
                        "default": 50,
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["text"]
            }
        ),
        Tool(
            name="skill_list",
            description="List all available skill categories",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="skill_get_template",
            description="Get skill template by category name",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Skill category name",
                        "enum": ["legal", "technical", "medical", "academic", "textbook", "general"]
                    },
                    "template_type": {
                        "type": "string",
                        "description": "Type of template to retrieve",
                        "enum": ["quiz_generation", "summary", "translation"],
                        "default": "quiz_generation"
                    }
                },
                "required": ["category"]
            }
        ),
        Tool(
            name="skill_list_templates",
            description="List all available skill templates",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="skill_get_categories",
            description="Get all skill categories with their keywords",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Specific category to get keywords for (optional)"
                    }
                },
                "required": []
            }
        ),
    ]