# -*- coding: utf-8 -*-
"""
================================================================================
MCP FAZA 7 TESTS
================================================================================
Testovi za FAZA 7 MCP alate - Quiz, Translation, Document i Skills.
Pokretanje:
    pytest mcp-server/tests/test_mcp_faza7.py -v
================================================================================
"""

import pytest
from ai_learning_mcp.tools import (
    get_quiz_tools,
    get_translate_tools,
    get_document_tools,
    get_skill_tools,
)
from ai_learning_mcp.tools import (
    quiz_handlers,
    translate_handlers,
    document_handlers,
    skills_handlers,
)


class TestQuizTools:
    """Testovi za Quiz MCP alate."""

    def test_get_quiz_tools(self):
        """Test da se vraća lista Quiz alata."""
        tools = get_quiz_tools()
        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "quiz_create" in tool_names
        assert "quiz_list" in tool_names
        assert "quiz_get" in tool_names
        assert "quiz_submit_attempt" in tool_names
        assert "quiz_get_providers" in tool_names

    def test_quiz_create_schema(self):
        """Test quiz_create input schema."""
        tools = get_quiz_tools()
        tool = next(t for t in tools if t.name == "quiz_create")
        schema = tool.inputSchema
        assert "document_id" in schema["properties"]
        assert "title" in schema["properties"]
        assert "num_questions" in schema["properties"]
        assert schema["properties"]["num_questions"].get("default") == 10


class TestTranslateTools:
    """Testovi za Translation MCP alate."""

    def test_get_translate_tools(self):
        """Test da se vraća lista Translation alata."""
        tools = get_translate_tools()
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "translate_text" in tool_names
        assert "translate_batch" in tool_names
        assert "translate_supported_languages" in tool_names

    def test_translate_text_schema(self):
        """Test translate_text input schema."""
        tools = get_translate_tools()
        tool = next(t for t in tools if t.name == "translate_text")
        schema = tool.inputSchema
        assert "text" in schema["properties"]
        assert "source_language" in schema["properties"]
        assert "target_language" in schema["properties"]


class TestDocumentTools:
    """Testovi za Document MCP alate."""

    def test_get_document_tools(self):
        """Test da se vraća lista Document alata."""
        tools = get_document_tools()
        assert len(tools) == 4
        tool_names = [t.name for t in tools]
        assert "document_process" in tool_names
        assert "document_detect_skill" in tool_names
        assert "document_list" in tool_names
        assert "document_get_chunks" in tool_names


class TestSkillsTools:
    """Testovi za Skills MCP alate."""

    def test_get_skill_tools(self):
        """Test da se vraća lista Skills alata."""
        tools = get_skill_tools()
        assert len(tools) == 5
        tool_names = [t.name for t in tools]
        assert "skill_detect" in tool_names
        assert "skill_list" in tool_names
        assert "skill_get_template" in tool_names
        assert "skill_list_templates" in tool_names
        assert "skill_get_categories" in tool_names


class TestSkillsHandlers:
    """Testovi za Skills handler logiku."""

    def test_detect_category_legal(self):
        """Test detekcije pravnog dokumenta."""
        text = "This agreement establishes the terms and conditions between the parties. Section 1 defines the obligations. The termination clause specifies the deadline for notice."
        result = skills_handlers.detect_category(text, threshold=50)
        assert result["category"] == "legal"
        assert result["confidence"] > 0

    def test_detect_category_technical(self):
        """Test detekcije tehničkog dokumenta."""
        text = "This API documentation describes the installation and configuration parameters. The error codes are listed below. Follow the setup guide for troubleshooting."
        result = skills_handlers.detect_category(text, threshold=50)
        assert result["category"] == "technical"
        assert result["confidence"] > 0

    def test_detect_category_medical(self):
        """Test detekcije medicinskog dokumenta."""
        text = "The patient presents with symptoms of fever and cough. Treatment includes medication and therapy. Clinical diagnosis indicates the condition."
        result = skills_handlers.detect_category(text, threshold=50)
        assert result["category"] == "medical"
        assert result["confidence"] > 0

    def test_detect_category_academic(self):
        """Test detekcije akademskog rada."""
        text = "This research paper presents methodology and findings. Statistical analysis shows significant results. The sample size was 100 participants."
        result = skills_handlers.detect_category(text, threshold=50)
        assert result["category"] == "academic"
        assert result["confidence"] > 0

    def test_skill_list(self):
        """Test liste kategorija."""
        result = skills_handlers.handle_skill_list()
        assert result["status"] == "ok"
        assert "legal" in result["categories"]
        assert "technical" in result["categories"]
        assert "medical" in result["categories"]
        assert "academic" in result["categories"]

    def test_skill_get_template(self):
        """Test dobijanja template-a."""
        result = skills_handlers.handle_skill_get_template(
            {"category": "legal", "template_type": "quiz_generation"}
        )
        assert result["status"] == "ok"
        assert result["category"] == "legal"
        assert "template" in result

    def test_skill_get_categories(self):
        """Test dobijanja kategorija sa ključnim rečima."""
        result = skills_handlers.handle_skill_get_categories({})
        assert result["status"] == "ok"
        assert "legal" in result["categories"]
        assert "technical" in result["categories"]


class TestTranslateHandlers:
    """Testovi za Translation handlere."""

    def test_supported_languages(self):
        """Test podržanih jezika."""
        result = translate_handlers.handle_translate_supported_languages()
        assert result["status"] == "ok"
        assert len(result["languages"]) > 0
        lang_codes = [l["code"] for l in result["languages"]]
        assert "en" in lang_codes
        assert "sr" in lang_codes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
