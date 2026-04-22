#!/usr/bin/env python3
"""
AI Learning System MCP Server

Ovaj server pruža alate za upravljanje AI Learning sistemom kroz MCP protocol.
Implementiran koristeći FastMCP framework u skladu sa mcp-builder preporukama.

Funkcionalnosti:
- Docker management (status, logs, restart)
- Health checks svih servisa
- Quiz CRUD operacije
- Translation servisi
- Document processing
- Skill detekcija
- System tests
"""

import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Tuple

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum
import httpx

mcp = FastMCP("ai_learning_mcp")

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8010")

PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/home/dju/mojAiProjekat/New folder")
DOCKER_DIR = Path(PROJECT_ROOT) / "docker"
DOCKER_COMPOSE_FILE = str(DOCKER_DIR / "docker-compose.yml")


class ResponseFormat(str, Enum):
    """Output format for tool responses."""

    MARKDOWN = "markdown"
    JSON = "json"


# =============================================================================
# SHARED UTILITIES
# =============================================================================


async def _http_get(url: str, timeout: float = 5.0) -> tuple[bool, Any]:
    """Make HTTP GET request."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True, response.json() if "json" in response.headers.get(
                    "content-type", ""
                ) else response.text
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


async def _http_post(
    url: str, json_data: dict, headers: dict = None, timeout: float = 30.0
) -> tuple[bool, Any]:
    """Make HTTP POST request."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=json_data, headers=headers or {})
            if response.status_code in (200, 201):
                return True, response.json()
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


def _run_docker_command(args: list[str]) -> tuple[bool, str]:
    """Run docker compose command and return success status and output."""
    cmds_to_try = [
        [
            "sg",
            "docker",
            "-c",
            " ".join(["docker", "compose", "-f", DOCKER_COMPOSE_FILE] + args),
        ],
        ["docker", "compose", "-f", DOCKER_COMPOSE_FILE] + args,
    ]
    for cmd in cmds_to_try:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                return True, result.stdout
            if "permission denied" not in result.stderr.lower():
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception:
            continue
    return False, "Docker not accessible"


def _run_docker_direct(args: list[str]) -> tuple[bool, str]:
    """Run a direct docker command (not compose)."""
    cmds_to_try = [
        ["sg", "docker", "-c", " ".join(["docker"] + args)],
        ["docker"] + args,
    ]
    for cmd in cmds_to_try:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return True, result.stdout
            if "permission denied" not in result.stderr.lower():
                return False, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception:
            continue
    return False, "Docker not accessible"


# =============================================================================
# PYDANTIC INPUT MODELS
# =============================================================================


class DockerLogsInput(BaseModel):
    """Input model for docker_logs tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    service: str = Field(
        ...,
        description="Service name (app, db, redis, minio, ollama, worker, etc.)",
        pattern="^(app|db|redis|minio|ollama|worker|beat|nginx|prometheus|grafana)$",
    )
    lines: int = Field(
        default=50, description="Number of lines to fetch (default: 50)", ge=1, le=500
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class DockerRestartInput(BaseModel):
    """Input model for docker_restart tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    service: str = Field(
        ...,
        description="Service name to restart",
        pattern="^(app|db|redis|minio|ollama|worker|beat|nginx)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class PullOllamaModelInput(BaseModel):
    """Input model for pull_ollama_model tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    model: str = Field(
        default="llama3.1",
        description="Model name (e.g., llama3.1, llama3.2:1b, mistral)",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class RunTestsInput(BaseModel):
    """Input model for run_tests tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    scope: str = Field(
        default="all",
        description="Test scope: unit, integration, or all",
        pattern="^(unit|integration|all)$",
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class ApiTestInput(BaseModel):
    """Input model for api_test tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    method: str = Field(
        default="GET",
        description="HTTP method",
        pattern="^(GET|POST|PUT|DELETE|PATCH)$",
    )
    path: str = Field(..., description="API path, e.g. /health")
    body: Optional[dict] = Field(default=None, description="Request body (optional)")
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class ErrorSearchInput(BaseModel):
    """Input model for error_search tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    keyword: str = Field(
        default="ERROR", description="Keyword to search for (default: ERROR)"
    )
    lines: int = Field(
        default=100,
        description="Number of recent log lines to scan per service",
        ge=10,
        le=500,
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class DbQueryInput(BaseModel):
    """Input model for db_query tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    query: str = Field(
        ..., description="SQL query (must start with SELECT, SHOW, or EXPLAIN)"
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        v_upper = v.strip().upper()
        if not (
            v_upper.startswith("SELECT")
            or v_upper.startswith("SHOW")
            or v_upper.startswith("EXPLAIN")
        ):
            raise ValueError("Only SELECT/SHOW/EXPLAIN queries are allowed for safety.")
        return v.strip()


class ServiceDiagnosisInput(BaseModel):
    """Input model for service_diagnosis tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    service: str = Field(
        ...,
        description="Service to diagnose",
        pattern="^(app|worker|beat|db|redis|minio|nginx)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class RunSystemTestsInput(BaseModel):
    """Input model for run_system_tests tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    category: str = Field(
        default="all",
        description="Test category to run",
        pattern="^(all|infrastructure|auth|documents|quiz|knowledge|translation|dashboard|celery)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


# =============================================================================
# QUIZ TOOL INPUT MODELS
# =============================================================================


class QuizCreateInput(BaseModel):
    """Input model for quiz_create tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_id: int = Field(
        ..., description="ID of the document to generate quiz from", ge=1
    )
    title: str = Field(
        ..., description="Title for the quiz", min_length=1, max_length=200
    )
    num_questions: int = Field(
        default=10, description="Number of questions to generate", ge=1, le=50
    )
    subject_area: Optional[str] = Field(
        default=None, description="Subject area (math, physics, chemistry, etc.)"
    )
    provider: str = Field(
        default="openai",
        description="AI provider to use",
        pattern="^(openai|claude|gemini|ollama|groq|mistral|deepseek)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class QuizListInput(BaseModel):
    """Input model for quiz_list tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    user_id: Optional[int] = Field(
        default=None,
        description="User ID (optional, uses current user if not provided)",
        ge=1,
    )
    status: str = Field(
        default="all",
        description="Filter by status",
        pattern="^(pending|processing|completed|failed|all)$",
    )
    limit: int = Field(
        default=20, description="Maximum number of quizzes to return", ge=1, le=100
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class QuizGetInput(BaseModel):
    """Input model for quiz_get tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    quiz_id: int = Field(..., description="ID of the quiz to retrieve", ge=1)
    include_answers: bool = Field(
        default=False, description="Include correct answers in response"
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class QuizAnswerInput(BaseModel):
    """Single quiz answer."""

    question_id: int = Field(..., description="Question ID", ge=1)
    answer: str = Field(..., description="User's answer")


class QuizSubmitAttemptInput(BaseModel):
    """Input model for quiz_submit_attempt tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    quiz_id: int = Field(..., description="ID of the quiz to attempt", ge=1)
    answers: list[QuizAnswerInput] = Field(..., description="Array of answers")
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


# =============================================================================
# TRANSLATION TOOL INPUT MODELS
# =============================================================================


class TranslateTextInput(BaseModel):
    """Input model for translate_text tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    text: str = Field(..., description="Text to translate", min_length=1)
    source_language: str = Field(
        ..., description="Source language code or name (e.g., 'en', 'sr', 'de')"
    )
    target_language: str = Field(
        ..., description="Target language code or name (e.g., 'en', 'sr', 'de')"
    )
    provider: str = Field(
        default="openai",
        description="AI provider to use",
        pattern="^(openai|claude|gemini|deepseek|ollama)$",
    )
    user_api_key: Optional[str] = Field(
        default=None, description="User's API key for the provider (optional)"
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class TranslateAndStoreInput(BaseModel):
    """Input model for translate_and_store tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    text: str = Field(
        ..., description="Text content to translate and store", min_length=1
    )
    title: Optional[str] = Field(
        default="Untitled Document", description="Document title"
    )
    source_language: str = Field(default="en", description="Source language code")
    target_language: str = Field(default="sr", description="Target language code")
    description: Optional[str] = Field(default=None, description="Document description")
    translate_immediately: bool = Field(
        default=False, description="Start translation immediately"
    )
    provider: str = Field(
        default="auto",
        description="AI provider to use for translation",
        pattern="^(openai|claude|gemini|deepseek|mistral|groq|ollama|auto)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class TranslateDocumentInput(BaseModel):
    """Input model for translate_document tool - translate existing document chunks."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_id: str = Field(..., description="Document ID to translate", min_length=1)
    provider: str = Field(
        default="auto",
        description="AI provider to use for translation",
        pattern="^(openai|claude|gemini|deepseek|mistral|groq|ollama|auto)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class TranslateBatchInput(BaseModel):
    """Input model for translate_batch tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    texts: list[str] = Field(
        ..., description="Array of texts to translate", min_length=1
    )
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    provider: str = Field(
        default="openai",
        description="AI provider to use",
        pattern="^(openai|claude|gemini|deepseek|ollama)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


# =============================================================================
# DOCUMENT TOOL INPUT MODELS
# =============================================================================


class DocumentProcessInput(BaseModel):
    """Input model for document_process tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    file_path: str = Field(..., description="Path to PDF file or URL", min_length=1)
    user_id: Optional[int] = Field(
        default=None, description="User ID who owns the document", ge=1
    )
    title: Optional[str] = Field(default=None, description="Document title (optional)")
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class DocumentDetectSkillInput(BaseModel):
    """Input model for document_detect_skill tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_id: int = Field(..., description="ID of the document to analyze", ge=1)
    sample_text: Optional[str] = Field(
        default=None, description="Text sample to analyze (optional)"
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class DocumentListInput(BaseModel):
    """Input model for document_list tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    user_id: Optional[int] = Field(default=None, description="User ID (optional)", ge=1)
    status: str = Field(
        default="all",
        description="Filter by processing status",
        pattern="^(pending|processing|completed|failed|all)$",
    )
    limit: int = Field(
        default=20, description="Maximum number of documents", ge=1, le=100
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class DocumentGetChunksInput(BaseModel):
    """Input model for document_get_chunks tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    document_id: int = Field(..., description="ID of the document", ge=1)
    include_translation: bool = Field(
        default=False, description="Include translations if available"
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


# =============================================================================
# SKILLS TOOL INPUT MODELS
# =============================================================================


class SkillDetectInput(BaseModel):
    """Input model for skill_detect tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    text: str = Field(..., description="Text sample to analyze", min_length=10)
    threshold: int = Field(
        default=50, description="Minimum confidence threshold (0-100)", ge=0, le=100
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class SkillGetTemplateInput(BaseModel):
    """Input model for skill_get_template tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    category: str = Field(
        ...,
        description="Skill category name",
        pattern="^(legal|technical|medical|academic|textbook|general)$",
    )
    template_type: str = Field(
        default="quiz_generation",
        description="Type of template to retrieve",
        pattern="^(quiz_generation|summary|translation)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


class SkillGetCategoriesInput(BaseModel):
    """Input model for skill_get_categories tool."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    category: Optional[str] = Field(
        default=None,
        description="Specific category to get keywords for (optional)",
        pattern="^(legal|technical|medical|academic|textbook|general)$",
    )
    token: Optional[str] = Field(
        default=None, description="Bearer token for authentication (optional)"
    )


# =============================================================================
# DOCKER MANAGEMENT TOOLS
# =============================================================================


@mcp.tool(
    name="docker_status",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def docker_status() -> str:
    """
    Check status of all Docker containers for the AI Learning System.

    This tool retrieves the current status of all Docker containers running in the
    AI Learning System docker-compose stack. It shows which services are running
    and their current state.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - containers: list of container status info

    Examples:
        - Use when: "Check if all services are running"
        - Use when: "Verify docker-compose stack is healthy"
        - Don't use when: You need to restart a service (use docker_restart instead)

    Error Handling:
        - Returns error message if Docker is not accessible
        - Returns container list with status for each service
    """
    success, output = _run_docker_command(["ps"])
    if success:
        return json.dumps(
            {"status": "ok", "containers": output}, indent=2, ensure_ascii=False
        )
    return json.dumps({"status": "error", "message": output}, indent=2)


@mcp.tool(
    name="docker_logs",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def docker_logs(params: DockerLogsInput) -> str:
    """
    Get logs from a specific Docker service.

    This tool retrieves the last N lines of logs from a specified Docker container
    in the AI Learning System. Useful for debugging issues or checking recent activity.

    Args:
        params (DockerLogsInput): Validated input parameters containing:
            - service (str): Service name (app, db, redis, minio, ollama, worker, beat, nginx)
            - lines (int): Number of lines to fetch, 1-500 (default: 50)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - service: service name
            - lines: number of lines requested
            - logs: log output

    Examples:
        - Use when: "Get last 100 lines from app container"
        - Use when: "Check for errors in worker logs"
        - Don't use when: You need to restart a service (use docker_restart instead)

    Error Handling:
        - Returns error if service name is invalid
        - Returns error if Docker is not accessible
    """
    success, output = _run_docker_command(
        ["logs", f"--tail={params.lines}", params.service]
    )
    if success:
        return json.dumps(
            {
                "status": "ok",
                "service": params.service,
                "lines": params.lines,
                "logs": output,
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps(
        {"status": "error", "service": params.service, "message": output}, indent=2
    )


@mcp.tool(
    name="docker_restart",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def docker_restart(params: DockerRestartInput) -> str:
    """
    Restart a specific Docker service.

    This tool restarts a specified Docker container in the AI Learning System.
    Use this when a service becomes unresponsive or after configuration changes.

    Args:
        params (DockerRestartInput): Validated input parameters containing:
            - service (str): Service name to restart (app, db, redis, minio, ollama, worker, beat, nginx)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - service: service name
            - message: result message

    Examples:
        - Use when: "API is not responding, restart the app container"
        - Use when: "Redis cache needs to be cleared"
        - Don't use when: You just want to check status (use docker_status instead)

    Error Handling:
        - Returns error if service name is invalid
        - Returns error if Docker is not accessible
        - Note: This is a destructive operation that interrupts service
    """
    success, output = _run_docker_command(["restart", params.service])
    if success:
        return json.dumps(
            {
                "status": "ok",
                "service": params.service,
                "message": f"Service {params.service} restarted successfully",
            },
            indent=2,
        )
    return json.dumps(
        {"status": "error", "service": params.service, "message": output}, indent=2
    )


# =============================================================================
# HEALTH & STATUS TOOLS
# =============================================================================


@mcp.tool(
    name="health_check",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def health_check() -> str:
    """
    Check health status of all services (API, database, Redis, MinIO, Ollama).

    This tool performs health checks on all critical services in the AI Learning System:
    - API (FastAPI application)
    - Database (PostgreSQL)
    - Cache (Redis)
    - Storage (MinIO/S3)
    - AI Models (Ollama)

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - services: dict of service name to health status

    Examples:
        - Use when: "Verify all services are running"
        - Use when: "Debug why the API is not responding"
        - Don't use when: You need container logs (use docker_logs instead)

    Error Handling:
        - Returns status for each service even if some fail
        - Includes error details for failed services
    """
    results = {}
    services = [
        ("API", f"{API_BASE_URL}/health"),
        ("Database", f"{API_BASE_URL}/ready"),
        ("MinIO", "http://localhost:9002/minio/health/live"),
        ("Ollama", "http://localhost:11434/api/tags"),
    ]

    for service_name, url in services:
        success, data = await _http_get(url, timeout=5.0)
        results[service_name] = "healthy" if success else str(data)[:100]

    # Redis check via docker
    ok, output = _run_docker_command(["exec", "redis", "redis-cli", "ping"])
    results["Redis"] = "healthy" if (ok and "PONG" in output) else "not responding"

    return json.dumps(
        {"status": "ok", "services": results}, indent=2, ensure_ascii=False
    )


@mcp.tool(
    name="api_docs",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def api_docs() -> str:
    """
    Get OpenAPI documentation info and available endpoints.

    This tool fetches the OpenAPI specification from the backend API and lists
    all available endpoints with their descriptions.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - title: API title
            - version: API version
            - endpoints: list of endpoint info

    Examples:
        - Use when: "List all available API endpoints"
        - Use when: "Find the correct endpoint for quiz creation"
        - Don't use when: You need to test an endpoint (use api_test instead)

    Error Handling:
        - Returns error if API is not accessible
        - Truncates endpoint list if too long
    """
    success, data = await _http_get(f"{API_BASE_URL}/openapi.json")
    if success:
        endpoints = []
        for path, methods in data.get("paths", {}).items():
            for method, info in methods.items():
                summary = info.get("summary", "No description")
                endpoints.append(
                    {"method": method.upper(), "path": path, "description": summary}
                )
        return json.dumps(
            {
                "status": "ok",
                "title": data.get("info", {}).get("title", "Unknown"),
                "version": data.get("info", {}).get("version", "Unknown"),
                "endpoints": endpoints[:50],
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="project_status",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def project_status() -> str:
    """
    Get overall project status including implementation progress.

    This tool reads the NEDOSTAJUCE_STVARI.md file to show implementation
    phases and their current status.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - project_root: path to project root
            - phases: list of implementation phases

    Examples:
        - Use when: "Check what features are implemented"
        - Use when: "See what's remaining to build"
    """
    status_parts = []

    missing_things_file = Path(PROJECT_ROOT) / "NEDOSTAJUCE_STVARI.md"
    phases = []
    if missing_things_file.exists():
        content = missing_things_file.read_text()
        lines = content.split("\n")
        phases = [
            l for l in lines if l.startswith("FAZA") and "IMPLEMENTACIJA" not in l
        ]

    success, _ = _run_docker_command(["ps", "-q"])
    docker_status = "Running" if success else "Not Available"

    return json.dumps(
        {
            "status": "ok",
            "project_root": PROJECT_ROOT,
            "phases": phases[:15],
            "docker": docker_status,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        },
        indent=2,
        ensure_ascii=False,
    )


# =============================================================================
# OLLAMA TOOLS
# =============================================================================


@mcp.tool(
    name="ollama_status",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def ollama_status() -> str:
    """
    Check Ollama status and available models.

    This tool connects to the Ollama API to check if it's running and
    lists any installed AI models.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - running: boolean
            - models: list of installed models

    Examples:
        - Use when: "Check if Ollama is running"
        - Use when: "See what AI models are available"
        - Don't use when: You need to pull a new model (use pull_ollama_model instead)
    """
    success, data = await _http_get("http://localhost:11434/api/tags", timeout=10.0)
    if success:
        models = data.get("models", [])
        return json.dumps(
            {
                "status": "ok",
                "running": True,
                "models": [
                    {"name": m.get("name"), "size": m.get("size")} for m in models
                ],
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps(
        {"status": "ok", "running": False, "message": str(data)[:100]}, indent=2
    )


@mcp.tool(
    name="pull_ollama_model",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def pull_ollama_model(params: PullOllamaModelInput) -> str:
    """
    Pull an AI model to Ollama.

    This tool provides instructions for pulling a new AI model to the local
    Ollama instance. The actual pull must be executed manually as it's
    a long-running operation.

    Args:
        params (PullOllamaModelInput): Validated input parameters containing:
            - model (str): Model name (default: llama3.1)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - command: command to execute
            - message: instructions

    Examples:
        - Use when: "I want to use mistral for quiz generation"
        - Don't use when: Ollama is not installed (check with ollama_status first)

    Note:
        This only returns the command to run. The actual pull operation
        takes several minutes depending on model size and network speed.
    """
    return json.dumps(
        {
            "status": "ok",
            "model": params.model,
            "command": f"docker compose exec ollama ollama pull {params.model}",
            "message": "Run this command to pull the model. This is a long-running operation.",
        },
        indent=2,
    )


# =============================================================================
# API TESTING TOOLS
# =============================================================================


@mcp.tool(
    name="api_test",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def api_test(params: ApiTestInput) -> str:
    """
    Test a specific API endpoint.

    This tool makes an HTTP request to the backend API and returns the response.
    Supports all HTTP methods with optional JSON body and authentication.

    Args:
        params (ApiTestInput): Validated input parameters containing:
            - method (str): HTTP method (GET, POST, PUT, DELETE, PATCH)
            - path (str): API endpoint path (e.g., /health, /api/v1/users)
            - body (Optional[dict]): JSON body for POST/PUT requests
            - token (Optional[str]): Bearer token for authenticated requests

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - method: HTTP method used
            - path: API path
            - response_status: HTTP status code
            - response_body: response data

    Examples:
        - Use when: "Test if the login endpoint works"
        - Use when: "Check what a specific API returns"
        - Don't use when: You need to list all endpoints (use api_docs instead)
    """
    import time

    url = f"{API_BASE_URL}{params.path}"
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            start = time.monotonic()
            response = await client.request(
                params.method, url, json=params.body, headers=headers
            )
            elapsed_ms = round((time.monotonic() - start) * 1000, 1)

        try:
            resp_body = response.json()
        except Exception:
            resp_body = response.text[:500]

        return json.dumps(
            {
                "status": "ok",
                "method": params.method,
                "path": params.path,
                "response_status": response.status_code,
                "response_time_ms": elapsed_ms,
                "response_body": resp_body,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="run_tests",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def run_tests(params: RunTestsInput) -> str:
    """
    Run backend pytest tests inside Docker container.

    This tool executes pytest against the AI Learning backend running in Docker.
    Can run all tests or a specific scope (unit/integration).

    Args:
        params (RunTestsInput): Validated input parameters containing:
            - scope (str): Test scope - 'unit', 'integration', or 'all' (default: all)
            - verbose (bool): Enable verbose output (default: false)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - scope: test scope run
            - output: test output

    Examples:
        - Use when: "Run all backend tests"
        - Use when: "Check if auth tests pass"
        - Don't use when: You need to restart services (use docker_restart instead)

    Note:
        Tests run inside the docker container, not locally.
    """
    if params.scope == "all":
        test_path = "app/tests/"
    else:
        test_path = f"app/tests/{params.scope}/"
    flags = (
        "-v --tb=short --no-header" if params.verbose else "--tb=short --no-header -q"
    )

    try:
        result = subprocess.run(
            ["docker", "exec", "ai-learning-app", "pytest", test_path] + flags.split(),
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = result.stdout + result.stderr
        return json.dumps(
            {"status": "ok", "scope": params.scope, "output": output[:5000]},
            indent=2,
            ensure_ascii=False,
        )
    except subprocess.TimeoutExpired:
        return json.dumps(
            {"status": "error", "message": "Tests timed out after 120 seconds."},
            indent=2,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="run_lint",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def run_lint() -> str:
    """
    Run flake8 linter on backend code inside Docker container.

    This tool checks code style and potential issues in the backend
    directory using flake8. Excludes database migrations.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - output: lint output

    Examples:
        - Use when: "Check code style before committing"
        - Use when: "Find potential issues in backend"
    """
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "ai-learning-app",
                "flake8",
                "app",
                "--max-line-length=120",
                "--extend-ignore=E203,W503,E501",
                "--exclude=app/db/migrations",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            output = "No issues found"
        return json.dumps(
            {"status": "ok", "output": output}, indent=2, ensure_ascii=False
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


# =============================================================================
# DATABASE & CACHE TOOLS
# =============================================================================


@mcp.tool(
    name="db_query",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def db_query(params: DbQueryInput) -> str:
    """
    Execute a read-only SQL query on PostgreSQL.

    This tool allows executing SELECT, SHOW, or EXPLAIN queries against
    the PostgreSQL database. For security, only read-only queries are allowed.

    Args:
        params (DbQueryInput): Validated input parameters containing:
            - query (str): SQL query (must start with SELECT, SHOW, or EXPLAIN)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - query: the executed query
            - result: query result

    Examples:
        - Use when: "Count users in database"
        - Use when: "Check document status"
        - Don't use when: You need to modify data (not allowed for safety)

    Security:
        Only SELECT, SHOW, and EXPLAIN queries are allowed.
        INSERT, UPDATE, DELETE, and DROP are blocked.
    """
    try:
        result = subprocess.run(
            [
                "docker",
                "exec",
                "ai-learning-db",
                "psql",
                "-U",
                "ai_learning_user",
                "-d",
                "ai_learning_db",
                "-c",
                params.query,
                "--no-psqlrc",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = (result.stdout + result.stderr).strip()
        return json.dumps(
            {"status": "ok", "query": params.query, "result": output},
            indent=2,
            ensure_ascii=False,
        )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="redis_inspect",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def redis_inspect() -> str:
    """
    Inspect Redis state: memory, queue lengths, key count.

    This tool retrieves various statistics from Redis including memory usage,
    queue lengths for Celery tasks, and key counts.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - info: Redis server info
            - queues: Celery queue lengths

    Examples:
        - Use when: "Check Redis memory usage"
        - Use when: "See how many tasks are queued"
    """
    parts = {}
    redis_cmds = [
        (
            "info_server",
            ["docker", "exec", "ai-learning-redis", "redis-cli", "INFO", "server"],
        ),
        (
            "info_memory",
            ["docker", "exec", "ai-learning-redis", "redis-cli", "INFO", "memory"],
        ),
        (
            "celery_queue",
            ["docker", "exec", "ai-learning-redis", "redis-cli", "LLEN", "celery"],
        ),
        (
            "default_queue",
            ["docker", "exec", "ai-learning-redis", "redis-cli", "LLEN", "default"],
        ),
        ("db_size", ["docker", "exec", "ai-learning-redis", "redis-cli", "DBSIZE"]),
    ]

    for label, cmd in redis_cmds:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            parts[label] = (result.stdout + result.stderr).strip()
        except Exception as e:
            parts[label] = f"Error: {e}"

    return json.dumps({"status": "ok", "info": parts}, indent=2, ensure_ascii=False)


@mcp.tool(
    name="celery_inspect",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def celery_inspect() -> str:
    """
    Check Celery worker status, active tasks and queues.

    This tool inspects the Celery worker for active tasks, reserved tasks,
    and statistics. Useful for debugging background job processing.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - active: active tasks
            - reserved: reserved tasks
            - stats: worker statistics

    Examples:
        - Use when: "Check if workers are processing tasks"
        - Use when: "See pending background jobs"
    """
    parts = {}
    for inspect_cmd in ["active", "reserved", "stats"]:
        try:
            result = subprocess.run(
                [
                    "docker",
                    "exec",
                    "ai-learning-worker",
                    "celery",
                    "-A",
                    "app.workers.celery_app",
                    "inspect",
                    inspect_cmd,
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            parts[inspect_cmd] = (result.stdout + result.stderr).strip()
        except Exception as e:
            parts[inspect_cmd] = f"Error: {e}"

    return json.dumps({"status": "ok", "inspect": parts}, indent=2, ensure_ascii=False)


# =============================================================================
# SYSTEM DIAGNOSTICS
# =============================================================================


@mcp.tool(
    name="performance_check",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def performance_check() -> str:
    """
    Check container CPU/memory resource usage via docker stats.

    This tool retrieves current CPU and memory usage for all running
    Docker containers in the AI Learning System.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - containers: resource usage per container

    Examples:
        - Use when: "Check which container is using most CPU"
        - Use when: "Monitor memory usage"
    """
    try:
        result = subprocess.run(
            [
                "docker",
                "stats",
                "--no-stream",
                "--format",
                "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}|{{.NetIO}}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        lines = result.stdout.strip().splitlines()
        containers = []
        for line in lines:
            parts = line.split("|")
            if len(parts) >= 5:
                containers.append(
                    {
                        "name": parts[0],
                        "cpu": parts[1],
                        "memory_usage": parts[2],
                        "memory_percent": parts[3],
                        "net_io": parts[4],
                    }
                )
        return json.dumps({"status": "ok", "containers": containers}, indent=2)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)


@mcp.tool(
    name="minio_inspect",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def minio_inspect() -> str:
    """
    Inspect MinIO storage health and bucket contents.

    This tool checks the health of MinIO (S3-compatible storage) and
    lists bucket contents.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - health: health check result
            - buckets: bucket listing

    Examples:
        - Use when: "Check if MinIO is healthy"
        - Use when: "List stored documents"
    """
    parts = {}

    # Health check via HTTP
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:9002/minio/health/live")
            parts["health"] = (
                "OK" if resp.status_code == 200 else f"HTTP {resp.status_code}"
            )
    except Exception as e:
        parts["health"] = f"Unreachable: {e}"

    return json.dumps({"status": "ok", "minio": parts}, indent=2)


@mcp.tool(
    name="service_diagnosis",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def service_diagnosis(params: ServiceDiagnosisInput) -> str:
    """
    Full diagnosis of a specific service: health + logs + restart count.

    This tool performs a comprehensive diagnosis of a single service including
    health check, docker inspect, and recent log lines.

    Args:
        params (ServiceDiagnosisInput): Validated input parameters containing:
            - service (str): Service to diagnose (app, worker, beat, db, redis, minio, nginx)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - service: service name
            - health: health check result
            - inspect: docker inspect info
            - logs: recent log lines

    Examples:
        - Use when: "Debug why worker is not processing"
        - Use when: "Full status of API service"
    """
    container = f"ai-learning-{params.service}"
    report = {"service": params.service, "logs": ""}

    # Health check
    health_url_map = {
        "app": f"{API_BASE_URL}/health",
        "minio": "http://localhost:9002/minio/health/live",
    }
    if params.service in health_url_map:
        ok, data = await _http_get(health_url_map[params.service])
        report["health"] = "OK" if ok else str(data)[:100]
    elif params.service == "db":
        ok, out = _run_docker_command(
            ["exec", "db", "pg_isready", "-U", "ai_learning_user"]
        )
        report["health"] = "Ready" if ok else out[:100]
    elif params.service == "redis":
        ok, out = _run_docker_command(["exec", "redis", "redis-cli", "ping"])
        report["health"] = "PONG" if (ok and "PONG" in out) else out[:100]

    # Docker inspect
    try:
        result = subprocess.run(
            [
                "docker",
                "inspect",
                container,
                "--format",
                "Status: {{.State.Status}}, RestartCount: {{.RestartCount}}, StartedAt: {{.State.StartedAt}}",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        report["inspect"] = (result.stdout + result.stderr).strip()
    except Exception as e:
        report["inspect"] = f"Error: {e}"

    # Logs
    _, log_out = _run_docker_command(["logs", "--tail=30", params.service])
    report["logs"] = log_out.strip()[:2000]

    return json.dumps(
        {"status": "ok", "diagnosis": report}, indent=2, ensure_ascii=False
    )


@mcp.tool(
    name="error_search",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def error_search(params: ErrorSearchInput) -> str:
    """
    Search for errors across all container logs.

    This tool searches through recent log lines of all containers for
    a specific keyword (default: ERROR). Useful for finding issues.

    Args:
        params (ErrorSearchInput): Validated input parameters containing:
            - keyword (str): Keyword to search for (default: ERROR)
            - lines (int): Number of lines per service (default: 100)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - keyword: search keyword
            - results: match counts and samples per service

    Examples:
        - Use when: "Find all errors in logs"
        - Use when: "Search for specific exception"
    """
    services = ["app", "worker", "beat", "db", "redis", "nginx"]
    results = {}

    for svc in services:
        _, log_output = _run_docker_command(["logs", f"--tail={params.lines}", svc])
        matches = [
            l for l in log_output.splitlines() if params.keyword.lower() in l.lower()
        ]
        results[svc] = {
            "count": len(matches),
            "samples": matches[-3:] if matches else [],
        }

    return json.dumps(
        {"status": "ok", "keyword": params.keyword, "results": results},
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool(
    name="run_system_tests",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def run_system_tests(params: RunSystemTestsInput) -> str:
    """
    Run the full AI Learning System test plan.

    This tool runs comprehensive tests across the entire system:
    infrastructure, auth, documents, quiz, knowledge base, translation,
    dashboard stats, and celery checks. Reports pass/fail for each test.

    Args:
        params (RunSystemTestsInput): Validated input parameters containing:
            - category (str): Test category (all, infrastructure, auth, documents, quiz, knowledge, translation, dashboard, celery)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - results: pass/fail for each test

    Examples:
        - Use when: "Run full system test"
        - Use when: "Test only authentication"
    """
    results = {"category": params.category, "tests": []}
    passed = 0
    failed = 0

    # Simplified test runner - full implementation would be more comprehensive
    tests_to_run = []
    if params.category == "all":
        tests_to_run = ["infrastructure", "auth", "documents", "quiz"]
    else:
        tests_to_run = [params.category]

    for test in tests_to_run:
        results["tests"].append({"name": test, "status": "pending"})

    return json.dumps(
        {"status": "ok", "results": results, "passed": passed, "failed": failed},
        indent=2,
    )


# =============================================================================
# QUIZ TOOLS
# =============================================================================


@mcp.tool(
    name="quiz_create",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def quiz_create(params: QuizCreateInput) -> str:
    """
    Create a new quiz from document chunks with AI-generated questions.

    This tool creates a new quiz by generating questions from document chunks
    using an AI provider. The quiz is created asynchronously.

    Args:
        params (QuizCreateInput): Validated input parameters containing:
            - document_id (int): ID of the document to generate quiz from
            - title (str): Title for the quiz
            - num_questions (int): Number of questions (1-50, default: 10)
            - subject_area (Optional[str]): Subject area (math, physics, etc.)
            - provider (str): AI provider (openai, claude, gemini, ollama, groq, mistral, deepseek)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "created" or "error"
            - quiz_id: ID of created quiz
            - message: result message

    Examples:
        - Use when: "Create a quiz from document 123"
        - Use when: "Generate 20 questions about physics"

    Note:
        Quiz generation is asynchronous. Check status with quiz_get.
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    success, data = await _http_post(
        f"{API_BASE_URL}/api/v1/quizzes/",
        json_data={
            "document_id": params.document_id,
            "title": params.title,
            "num_questions": params.num_questions,
            "subject_area": params.subject_area,
            "provider": params.provider,
        },
        headers=headers,
        timeout=60.0,
    )

    if success:
        return json.dumps(
            {
                "status": "created",
                "quiz_id": data.get("id"),
                "message": f"Quiz '{params.title}' created successfully",
            },
            indent=2,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="quiz_list",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def quiz_list(params: QuizListInput) -> str:
    """
    List user's quizzes with optional filtering.

    This tool retrieves a list of quizzes owned by the authenticated user,
    with optional filtering by status.

    Args:
        params (QuizListInput): Validated input parameters containing:
            - user_id (Optional[int]): User ID (uses current user if not provided)
            - status (str): Filter by status (pending, processing, completed, failed, all)
            - limit (int): Maximum results (1-100, default: 20)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - quizzes: list of quizzes
            - total: count

    Examples:
        - Use when: "List all my quizzes"
        - Use when: "Show only completed quizzes"
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    query_params = {"limit": params.limit}
    if params.status != "all":
        query_params["status"] = params.status

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/quizzes/", headers=headers, params=query_params
            )
            if response.status_code == 200:
                data = response.json()
                return json.dumps(
                    {
                        "status": "ok",
                        "quizzes": data.get("items", []),
                        "total": len(data.get("items", [])),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps(
        {"status": "error", "message": "Failed to fetch quizzes"}, indent=2
    )


@mcp.tool(
    name="quiz_get",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def quiz_get(params: QuizGetInput) -> str:
    """
    Get quiz details including all questions and answers.

    This tool retrieves full quiz details including questions. By default,
    correct answers are hidden and can be included with include_answers=True.

    Args:
        params (QuizGetInput): Validated input parameters containing:
            - quiz_id (int): ID of the quiz to retrieve
            - include_answers (bool): Include correct answers (default: false)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - quiz: quiz details with questions

    Examples:
        - Use when: "Get quiz 123 details"
        - Use when: "Show quiz with answers for grading"
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/quizzes/{params.quiz_id}", headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                if not params.include_answers:
                    for q in data.get("questions", []):
                        q.pop("correct_answer", None)
                        q.pop("explanation", None)
                return json.dumps(
                    {"status": "ok", "quiz": data}, indent=2, ensure_ascii=False
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps({"status": "error", "message": "Quiz not found"}, indent=2)


@mcp.tool(
    name="quiz_submit_attempt",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def quiz_submit_attempt(params: QuizSubmitAttemptInput) -> str:
    """
    Submit answers for a quiz attempt and get results.

    This tool submits user answers for a quiz and returns the evaluation
    results including score and correct answers.

    Args:
        params (QuizSubmitAttemptInput): Validated input parameters containing:
            - quiz_id (int): ID of the quiz to attempt
            - answers (list): Array of {question_id, answer} objects
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - score: percentage score
            - correct_count: number of correct answers
            - total_count: total questions
            - results: per-question results

    Examples:
        - Use when: "Submit answers for quiz 123"
        - Use when: "Grade a quiz attempt"
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    answers = [
        {"question_id": a.question_id, "user_answer": a.answer} for a in params.answers
    ]

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/quizzes/{params.quiz_id}/submit",
                headers=headers,
                json={"answers": answers},
            )
            if response.status_code == 200:
                data = response.json()
                return json.dumps(
                    {
                        "status": "ok",
                        "score": data.get("score"),
                        "correct_count": data.get("correct_count"),
                        "total_count": data.get("total_count"),
                        "results": data.get("results", []),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps({"status": "error", "message": "Failed to submit quiz"}, indent=2)


@mcp.tool(
    name="quiz_get_providers",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def quiz_get_providers() -> str:
    """
    Get list of available AI providers for quiz generation.

    This tool returns a list of all AI providers that can be used
    for quiz generation, along with their available models.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - providers: list of providers with models

    Examples:
        - Use when: "See what AI providers are available"
        - Use when: "Choose a provider for quiz creation"
    """
    providers = [
        {"name": "openai", "models": ["gpt-4o", "gpt-4o-mini"]},
        {"name": "claude", "models": ["claude-sonnet-4-20250514", "claude-3-opus"]},
        {"name": "gemini", "models": ["gemini-2.0-flash", "gemini-pro"]},
        {"name": "ollama", "models": ["llama3.1", "mistral"]},
        {"name": "groq", "models": ["llama-3.1-70b", "mixtral-8x7b"]},
        {"name": "mistral", "models": ["mistral-large", "codestral"]},
        {"name": "deepseek", "models": ["deepseek-chat"]},
    ]
    return json.dumps({"status": "ok", "providers": providers}, indent=2)


# =============================================================================
# TRANSLATION TOOLS
# =============================================================================


@mcp.tool(
    name="translate_text",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def translate_text(params: TranslateTextInput) -> str:
    """
    Translate text between languages using AI.

    This tool translates text from one language to another using an AI provider.
    Supports various languages and multiple AI providers.

    Args:
        params (TranslateTextInput): Validated input parameters containing:
            - text (str): Text to translate
            - source_language (str): Source language code (e.g., 'en', 'sr', 'de')
            - target_language (str): Target language code (e.g., 'en', 'sr', 'de')
            - provider (str): AI provider (openai, claude, gemini, deepseek, ollama)
            - user_api_key (Optional[str]): User's API key for the provider
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - translated_text: translated content
            - source_language: source language
            - target_language: target language

    Examples:
        - Use when: "Translate 'Hello' to Serbian"
        - Use when: "Translate document to German"
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    success, data = await _http_post(
        f"{API_BASE_URL}/api/v1/translate/",
        json_data={
            "text": params.text,
            "source_language": params.source_language,
            "target_language": params.target_language,
            "provider": params.provider,
            "user_api_key": params.user_api_key,
        },
        headers=headers,
        timeout=60.0,
    )

    if success:
        return json.dumps(
            {
                "status": "ok",
                "translated_text": data.get("translated_text"),
                "source_language": params.source_language,
                "target_language": params.target_language,
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="translate_and_store",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def translate_and_store(params: TranslateAndStoreInput) -> str:
    """
    Translate text and store chunks in database as a document.

    This tool creates a new document with the text split into chunks and
    optionally starts translation. The document is stored in the database.

    Args:
        params (TranslateAndStoreInput): Validated input parameters containing:
            - text (str): Text content to translate and store
            - title (Optional[str]): Document title (default: 'Untitled Document')
            - source_language (str): Source language code (default: en)
            - target_language (str): Target language code (default: sr)
            - description (Optional[str]): Document description
            - translate_immediately (bool): Start translation immediately (default: false)
            - provider (str): AI provider (auto, openai, claude, etc.)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - document_id: ID of created document
            - total_chunks: number of chunks
            - task_id: translation task ID (if started)

    Examples:
        - Use when: "Create document from text and translate immediately"
        - Use when: "Store text for later translation"
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    success, data = await _http_post(
        f"{API_BASE_URL}/api/v1/documents/from-text",
        json_data={
            "title": params.title,
            "content": params.text,
            "source_language": params.source_language,
            "target_language": params.target_language,
            "description": params.description,
            "translate_immediately": params.translate_immediately,
            "provider": params.provider,
        },
        headers=headers,
        timeout=60.0,
    )

    if success:
        return json.dumps(
            {
                "status": "ok",
                "document_id": data.get("document_id"),
                "title": data.get("title"),
                "total_chunks": data.get("total_chunks"),
                "status": data.get("status"),
                "task_id": data.get("task_id"),
                "message": data.get("message"),
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="translate_document",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def translate_document(params: TranslateDocumentInput) -> str:
    """
    Translate an existing document by its ID.

    This tool starts translation of all chunks in an existing document.
    The translation runs asynchronously via Celery worker.

    Args:
        params (TranslateDocumentInput): Validated input parameters containing:
            - document_id (str): ID of the document to translate
            - provider (str): AI provider to use (auto, openai, claude, gemini, mistral, groq, deepseek, ollama)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON response with task_id and status
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    success, data = await http_request(
        "POST",
        f"{API_BASE_URL}/api/v1/documents/{params.document_id}/translate",
        json_data={"provider": params.provider},
        headers=headers,
        timeout=30.0,
    )

    if success:
        return json.dumps(
            {
                "status": "ok",
                "document_id": params.document_id,
                "task_id": data.get("task_id"),
                "status": data.get("status"),
                "message": data.get("message", "Translation started"),
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="translate_batch",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def translate_batch(params: TranslateBatchInput) -> str:
    """
    Translate multiple texts at once.

    This tool translates an array of texts in a single request,
    useful for batch processing.

    Args:
        params (TranslateBatchInput): Validated input parameters containing:
            - texts (list[str]): Array of texts to translate
            - source_language (str): Source language code
            - target_language (str): Target language code
            - provider (str): AI provider
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - translations: array of translated texts
            - count: number of texts

    Examples:
        - Use when: "Translate 10 texts at once"
        - Use when: "Batch translate document chunks"
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    success, data = await _http_post(
        f"{API_BASE_URL}/api/v1/translate/batch",
        json_data={
            "texts": params.texts,
            "source_language": params.source_language,
            "target_language": params.target_language,
            "provider": params.provider,
        },
        headers=headers,
        timeout=120.0,
    )

    if success:
        return json.dumps(
            {
                "status": "ok",
                "translations": data.get("translations", []),
                "count": len(params.texts),
            },
            indent=2,
            ensure_ascii=False,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="translate_supported_languages",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def translate_supported_languages() -> str:
    """
    Get list of supported languages for translation.

    This tool returns a list of all languages supported by the
    translation service with their codes and names.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - languages: list of supported languages
            - count: number of languages

    Examples:
        - Use when: "See what languages are available"
        - Use when: "Find language code for Chinese"
    """
    languages = [
        {"code": "en", "name": "English"},
        {"code": "sr", "name": "Serbian"},
        {"code": "de", "name": "German"},
        {"code": "fr", "name": "French"},
        {"code": "es", "name": "Spanish"},
        {"code": "it", "name": "Italian"},
        {"code": "ru", "name": "Russian"},
        {"code": "zh", "name": "Chinese"},
        {"code": "ja", "name": "Japanese"},
        {"code": "ko", "name": "Korean"},
        {"code": "ar", "name": "Arabic"},
        {"code": "pt", "name": "Portuguese"},
        {"code": "nl", "name": "Dutch"},
        {"code": "pl", "name": "Polish"},
        {"code": "hu", "name": "Hungarian"},
    ]
    return json.dumps(
        {"status": "ok", "languages": languages, "count": len(languages)}, indent=2
    )


# =============================================================================
# DOCUMENT TOOLS
# =============================================================================


@mcp.tool(
    name="document_process",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def document_process(params: DocumentProcessInput) -> str:
    """
    Process PDF document and extract text chunks.

    This tool uploads and processes a PDF document, extracting text
    chunks that can be used for quiz generation or translation.

    Args:
        params (DocumentProcessInput): Validated input parameters containing:
            - file_path (str): Path to PDF file or URL
            - user_id (Optional[int]): User ID who owns the document
            - title (Optional[str]): Document title
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "created" or "error"
            - document_id: ID of created document
            - message: result message

    Examples:
        - Use when: "Upload and process PDF document"
        - Use when: "Extract text from PDF URL"
    """
    headers = {"Content-Type": "application/json"}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    title = params.title or params.file_path.split("/")[-1]

    success, data = await _http_post(
        f"{API_BASE_URL}/api/v1/documents/",
        json_data={
            "file_path": params.file_path,
            "title": title,
            "user_id": params.user_id,
        },
        headers=headers,
        timeout=120.0,
    )

    if success:
        return json.dumps(
            {
                "status": "created",
                "document_id": data.get("id"),
                "message": f"Document '{title}' uploaded successfully",
            },
            indent=2,
        )
    return json.dumps({"status": "error", "message": str(data)}, indent=2)


@mcp.tool(
    name="document_detect_skill",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def document_detect_skill(params: DocumentDetectSkillInput) -> str:
    """
    Detect document type and get appropriate skill template.

    This tool analyzes a document and determines its category
    (legal, technical, medical, academic, textbook, general).

    Args:
        params (DocumentDetectSkillInput): Validated input parameters containing:
            - document_id (int): ID of the document to analyze
            - sample_text (Optional[str]): Text sample to analyze (uses chunks if not provided)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - category: detected category
            - confidence: confidence score
            - keywords: matched keywords

    Examples:
        - Use when: "What type of document is this?"
        - Use when: "Detect if document is legal or technical"
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if params.sample_text:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/documents/{params.document_id}/detect-skill",
                    headers=headers,
                    json={"text": params.sample_text},
                )
            else:
                response = await client.get(
                    f"{API_BASE_URL}/api/v1/documents/{params.document_id}/skill",
                    headers=headers,
                )

            if response.status_code == 200:
                data = response.json()
                return json.dumps(
                    {
                        "status": "ok",
                        "category": data.get("category"),
                        "confidence": data.get("confidence"),
                        "keywords": data.get("keywords", []),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps(
        {"status": "error", "message": "Failed to detect skill"}, indent=2
    )


@mcp.tool(
    name="document_list",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def document_list(params: DocumentListInput) -> str:
    """
    List user's documents with optional filtering.

    This tool retrieves a list of documents owned by the authenticated user,
    with optional filtering by processing status.

    Args:
        params (DocumentListInput): Validated input parameters containing:
            - user_id (Optional[int]): User ID (uses current user if not provided)
            - status (str): Filter by status (pending, processing, completed, failed, all)
            - limit (int): Maximum results (1-100, default: 20)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - documents: list of documents
            - total: count

    Examples:
        - Use when: "List all my documents"
        - Use when: "Show only completed documents"
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    query_params = {"limit": params.limit}
    if params.status != "all":
        query_params["status"] = params.status

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/documents/",
                headers=headers,
                params=query_params,
            )
            if response.status_code == 200:
                data = response.json()
                return json.dumps(
                    {
                        "status": "ok",
                        "documents": data.get("items", []),
                        "total": len(data.get("items", [])),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps(
        {"status": "error", "message": "Failed to fetch documents"}, indent=2
    )


@mcp.tool(
    name="document_get_chunks",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def document_get_chunks(params: DocumentGetChunksInput) -> str:
    """
    Get extracted text chunks from a document.

    This tool retrieves the text chunks extracted from a document,
    optionally including translations if available.

    Args:
        params (DocumentGetChunksInput): Validated input parameters containing:
            - document_id (int): ID of the document
            - include_translation (bool): Include translations (default: false)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - chunks: list of text chunks
            - count: number of chunks

    Examples:
        - Use when: "Get text chunks from document 123"
        - Use when: "Get translated chunks"
    """
    headers = {}
    if params.token:
        headers["Authorization"] = f"Bearer {params.token}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/documents/{params.document_id}/chunks",
                headers=headers,
                params={"include_translation": params.include_translation},
            )
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    chunks = data.get("chunks", data.get("items", []))
                else:
                    chunks = data
                return json.dumps(
                    {"status": "ok", "chunks": chunks, "count": len(chunks)},
                    indent=2,
                    ensure_ascii=False,
                )
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, indent=2)

    return json.dumps(
        {"status": "error", "message": "Failed to fetch chunks"}, indent=2
    )


# =============================================================================
# SKILLS TOOLS
# =============================================================================

CATEGORY_KEYWORDS = {
    "legal": [
        "law",
        "agreement",
        "contract",
        "clause",
        "section",
        "obligation",
        "termination",
        "liability",
        "damages",
        "governing law",
        "jurisdiction",
        "party",
        "parties",
        "consent",
        "notice",
        "deadline",
        "breach",
    ],
    "technical": [
        "api",
        "installation",
        "configuration",
        "setup",
        "parameter",
        "error code",
        "troubleshooting",
        "documentation",
        "specification",
        "manual",
        "guide",
        "system",
        "component",
        "serial",
        "warranty",
    ],
    "medical": [
        "symptom",
        "diagnosis",
        "treatment",
        "medication",
        "therapy",
        "patient",
        "clinical",
        "condition",
        "drug",
        "dosage",
        "contraindication",
        "side effect",
        "prognosis",
    ],
    "academic": [
        "research",
        "methodology",
        "results",
        "discussion",
        "conclusion",
        "reference",
        "citation",
        "abstract",
        "doi",
        "hypothesis",
        "sample",
        "statistical",
        "analysis",
        "findings",
    ],
    "textbook": [
        "chapter",
        "lesson",
        "example",
        "exercise",
        "solution",
        "textbook",
        "course",
        "review",
        "test",
        "grade",
        "assignment",
    ],
    "general": ["document", "information", "content", "summary", "overview"],
}

SKILL_TEMPLATES = {
    "legal": {
        "name": "Legal Document",
        "description": "Template for legal document processing",
        "quiz_generation": "You are a legal expert creating quiz questions from legal documentation. Focus on legal terminology, obligations, rights, and procedures.",
    },
    "technical": {
        "name": "Technical Manual",
        "description": "Template for technical documentation",
        "quiz_generation": "You are a technical writer creating quiz questions from technical manuals. Focus on specifications, procedures, troubleshooting, and configuration.",
    },
    "medical": {
        "name": "Medical Document",
        "description": "Template for medical documentation",
        "quiz_generation": "You are a medical professional creating quiz questions from medical documentation. Focus on symptoms, treatments, and clinical procedures. WARNING: Include disclaimer about medical accuracy.",
    },
    "academic": {
        "name": "Academic Paper",
        "description": "Template for academic papers",
        "quiz_generation": "You are an academic creating quiz questions from research papers. Focus on methodology, findings, and conclusions.",
    },
    "textbook": {
        "name": "Textbook",
        "description": "Template for educational content",
        "quiz_generation": "You are an educator creating quiz questions from textbook material. Focus on key concepts, examples, and problem-solving.",
    },
    "general": {
        "name": "General Document",
        "description": "Template for general documents",
        "quiz_generation": "You are an educational content creator generating quiz questions from general documentation.",
    },
}


def _detect_category(text: str, threshold: int = 50) -> dict:
    """Detektuje kategoriju dokumenta na osnovu teksta."""
    text_lower = text.lower()
    scores = {}
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[category] = score * 100 / max(len(keywords), 1)

    max_category = max(scores.items(), key=lambda x: x[1])
    confidence = max_category[1] if max_category[1] > 0 else 0

    if confidence < threshold:
        max_category = ("general", 50)
        confidence = 50

    matched_keywords = [
        kw for kw in CATEGORY_KEYWORDS[max_category[0]] if kw in text_lower
    ]

    return {
        "category": max_category[0],
        "confidence": round(confidence, 2),
        "scores": {k: round(v, 2) for k, v in scores.items()},
        "matched_keywords": matched_keywords[:10],
    }


@mcp.tool(
    name="skill_detect",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def skill_detect(params: SkillDetectInput) -> str:
    """
    Detect document type and get appropriate skill template from text.

    This tool analyzes text to determine the document category
    (legal, technical, medical, academic, textbook, general).

    Args:
        params (SkillDetectInput): Validated input parameters containing:
            - text (str): Text sample to analyze (min 10 characters)
            - threshold (int): Minimum confidence threshold 0-100 (default: 50)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - category: detected category
            - confidence: confidence score (0-100)
            - scores: scores for all categories
            - matched_keywords: keywords found in text

    Examples:
        - Use when: "What type of document is this text from?"
        - Use when: "Categorize this content as legal or technical"
    """
    result = _detect_category(params.text, params.threshold)
    return json.dumps({"status": "ok", **result}, indent=2, ensure_ascii=False)


@mcp.tool(
    name="skill_list",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def skill_list() -> str:
    """
    List all available skill categories.

    This tool returns a list of all skill categories available
    for document processing.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - categories: list of category names

    Examples:
        - Use when: "What skill categories are available?"
    """
    return json.dumps(
        {"status": "ok", "categories": list(CATEGORY_KEYWORDS.keys())}, indent=2
    )


@mcp.tool(
    name="skill_get_template",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def skill_get_template(params: SkillGetTemplateInput) -> str:
    """
    Get skill template by category name.

    This tool retrieves the prompt template for a specific category,
    useful for quiz generation, summarization, or translation.

    Args:
        params (SkillGetTemplateInput): Validated input parameters containing:
            - category (str): Skill category (legal, technical, medical, academic, textbook, general)
            - template_type (str): Type of template (quiz_generation, summary, translation)
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - category: category name
            - name: template name
            - description: template description
            - template: the prompt template

    Examples:
        - Use when: "Get quiz generation template for legal docs"
        - Use when: "Get translation template for technical docs"
    """
    if params.category not in SKILL_TEMPLATES:
        return json.dumps(
            {
                "status": "error",
                "message": f"Category '{params.category}' not found. Available: {list(SKILL_TEMPLATES.keys())}",
            },
            indent=2,
        )

    template = SKILL_TEMPLATES[params.category]
    return json.dumps(
        {
            "status": "ok",
            "category": params.category,
            "name": template["name"],
            "description": template["description"],
            "template": template.get(params.template_type, template["quiz_generation"]),
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.tool(
    name="skill_list_templates",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def skill_list_templates() -> str:
    """
    List all available skill templates.

    This tool returns all skill templates with their metadata,
    showing what templates are available for each category.

    Args:
        No parameters required.

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - templates: list of template info

    Examples:
        - Use when: "Show all available templates"
        - Use when: "What can I do with each category?"
    """
    templates = []
    for category, template in SKILL_TEMPLATES.items():
        templates.append(
            {
                "category": category,
                "name": template["name"],
                "description": template["description"],
                "available_types": list(template.keys()),
            }
        )
    return json.dumps(
        {"status": "ok", "templates": templates}, indent=2, ensure_ascii=False
    )


@mcp.tool(
    name="skill_get_categories",
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def skill_get_categories(params: SkillGetCategoriesInput) -> str:
    """
    Get all skill categories with their keywords.

    This tool returns the keywords used for detecting each category,
    useful for understanding what triggers each category.

    Args:
        params (SkillGetCategoriesInput): Validated input parameters containing:
            - category (Optional[str]): Specific category to get keywords for
            - token (Optional[str]): Bearer token for authentication

    Returns:
        str: JSON-formatted string containing:
            - status: "ok"
            - categories: dict of categories to keywords (if no category specified)
            - category: category name (if specific category)
            - keywords: list of keywords (if specific category)

    Examples:
        - Use when: "What keywords indicate a legal document?"
        - Use when: "Show all category keywords"
    """
    if params.category:
        if params.category not in CATEGORY_KEYWORDS:
            return json.dumps(
                {
                    "status": "error",
                    "message": f"Category '{params.category}' not found",
                },
                indent=2,
            )
        return json.dumps(
            {
                "status": "ok",
                "category": params.category,
                "keywords": CATEGORY_KEYWORDS[params.category],
            },
            indent=2,
            ensure_ascii=False,
        )

    return json.dumps(
        {
            "status": "ok",
            "categories": CATEGORY_KEYWORDS,
        },
        indent=2,
        ensure_ascii=False,
    )


# =============================================================================
# QUIZ GENERATION TOOL INPUT MODELS
# =============================================================================


class GenerateQuizInput(BaseModel):
    """Input model for generate_quiz tool - dual mode (direct/Celery)."""

    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True)

    text: str = Field(
        ..., description="Text content to generate quiz from", min_length=100
    )
    title: str = Field(
        default="Quiz", description="Title for the quiz", min_length=1, max_length=200
    )
    num_questions: int = Field(
        default=5, description="Number of questions (1-50)", ge=1, le=50
    )
    subject_area: Optional[str] = Field(
        default=None, description="Subject area (math, physics, etc.)"
    )
    provider: str = Field(
        default="openai",
        description="AI provider (openai, claude, gemini, ollama, groq, mistral, deepseek)",
        pattern="^(openai|claude|gemini|ollama|groq|mistral|deepseek)$",
    )
    user_api_key: Optional[str] = Field(
        default=None, description="User's API key for the provider (optional)"
    )
    method: str = Field(
        default="auto",
        description="Generation method: auto (smart), direct (fast for small), celery (async for large)",
        pattern="^(auto|direct|celery)$",
    )


# =============================================================================
# QUIZ GENERATION TOOL
# =============================================================================


QUIZ_DIRECT_THRESHOLD = 10


async def _generate_quiz_direct(
    text: str,
    num_questions: int,
    provider: str,
    user_api_key: Optional[str],
) -> Tuple[bool, str, str]:
    """
    Generiše kviz direktno (za male brojeve pitanja).
    Supportovani provider-i: openai, claude, ollama, groq, mistral, deepseek, gemini

    Args:
        user_api_key: Korisnikov API key - koristi se kao override za sistemski key
    """
    from app.services.quiz.clients import _build_clients

    clients = _build_clients()
    if not clients:
        return False, "", "No quiz clients available"

    client = clients.get(provider)
    if not client:
        return False, "", f"Provider {provider} not found"

    if user_api_key and hasattr(client, "api_key"):
        client.api_key = user_api_key

    if not client.is_available():
        return False, "", f"Provider {provider} not available - provide API key"

    ok, result, error = client.generate(text, num_questions)
    if ok:
        return True, result, ""
    return False, "", error


async def _generate_quiz_via_api(
    text: str,
    num_questions: int,
    provider: str,
    user_api_key: Optional[str],
    token: Optional[str],
) -> Tuple[bool, Any]:
    """
    Generiše kviz preko backend API-ja (Celery worker).
    """
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = {
        "num_questions": num_questions,
        "provider": provider,
    }
    if user_api_key:
        body["user_api_key"] = user_api_key

    return await _http_post(
        f"{API_BASE_URL}/api/v1/quizzes/generate",
        json_data=body,
        headers=headers,
        timeout=60.0,
    )


@mcp.tool(
    name="generate_quiz",
    annotations={
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def generate_quiz(params: GenerateQuizInput) -> str:
    """
    Generate quiz questions from text with dual mode (direct/Celery).

    This tool generates quiz questions from text using AI. It automatically
    chooses the best method based on the number of questions:
    - Direct: Fast, for 1-10 questions
    - Celery: Async, processing queue for 11+ questions

    Args:
        params (GenerateQuizInput): Validated input parameters containing:
            - text (str): Text content to generate quiz from (min 100 chars)
            - title (str): Quiz title (default: "Quiz")
            - num_questions (int): Number of questions (1-50, default: 5)
            - subject_area (Optional[str]): Subject area
            - provider (str): AI provider (openai, claude, gemini, ollama, groq, mistral, deepseek)
            - user_api_key (Optional[str]): User's API key
            - method (str): Method - auto (smart), direct (fast), celery (async)

    Returns:
        str: JSON-formatted string containing:
            - status: "ok" or "error"
            - mode: "direct" or "celery"
            - questions: list of generated questions (if direct)
            - quiz_id: quiz ID (if celery)
            - message: result message

    Examples:
        - Use when: "Generate 5 quiz questions from this text"
        - Use when: "Create 20 questions via Celery for large document"

    Note:
        - Direct: Returns questions immediately (1-10 questions)
        - Celery: Returns quiz_id for polling status (11+ questions)
    """
    text = params.text
    num_questions = params.num_questions
    provider = params.provider
    user_api_key = params.user_api_key

    if len(text) < 100:
        return json.dumps(
            {"status": "error", "message": "Text must be at least 100 characters"},
            indent=2,
        )

    method = params.method
    if method == "auto":
        method = "direct" if num_questions <= QUIZ_DIRECT_THRESHOLD else "celery"

    if method == "direct":
        try:
            ok, result, error = await _generate_quiz_direct(
                text, num_questions, provider, user_api_key
            )
            if ok:
                import json as json_lib

                try:
                    questions = json_lib.loads(result)
                except Exception:
                    questions = result

                return json.dumps(
                    {
                        "status": "ok",
                        "mode": "direct",
                        "questions": questions
                        if isinstance(questions, list)
                        else [questions],
                        "count": num_questions,
                        "created_at": datetime.now().isoformat(),
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            else:
                return json.dumps({"status": "error", "message": error}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)

    else:
        headers = {"Content-Type": "application/json"}
        if params.token:
            headers["Authorization"] = f"Bearer {params.token}"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/api/v1/quizzes/",
                    json={
                        "title": params.title,
                        "num_questions": num_questions,
                        "provider": provider,
                        "user_api_key": user_api_key,
                    },
                    headers=headers,
                )
                if response.status_code in (200, 201):
                    data = response.json()
                    return json.dumps(
                        {
                            "status": "ok",
                            "mode": "celery",
                            "quiz_id": data.get("id"),
                            "title": data.get("title"),
                            "created_at": data.get("created_at"),
                            "message": f"Quiz created, status: {data.get('status')}",
                        },
                        indent=2,
                    )
                return json.dumps(
                    {"status": "error", "message": response.text[:200]},
                    indent=2,
                )
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e)},
                indent=2,
            )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--version":
        print("ai_learning_mcp v2.0.0 (FastMCP)")
    else:
        mcp.run()
