# -*- coding: utf-8 -*-
"""
AI Learning MCP Tools Package
FAZA 7: Quiz, Translation, Document i Skills MCP tools.
"""

from .quiz import get_quiz_tools
from .translate import get_translate_tools
from .document import get_document_tools
from .skills import get_skill_tools

__all__ = [
    "get_quiz_tools",
    "get_translate_tools",
    "get_document_tools",
    "get_skill_tools",
]
