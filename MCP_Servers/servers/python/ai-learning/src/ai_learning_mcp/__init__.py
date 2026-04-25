"""
AI Learning System MCP Server
Provides tools, resources, and prompts for project monitoring and management.
Fully compliant with Model Context Protocol specification.
"""

import os
import sys
import json
import logging
import subprocess
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, Resource, TextContent, Prompt, PromptMessage, EmbeddedResource
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("ai-learning-mcp")

APP_NAME = "ai-learning-mcp"
PROJECT_ROOT = Path("/home/dju/Projekti/AI SISTEM ZA UCENJE/ai-learning-system")
DOCKER_DIR = PROJECT_ROOT / "docker"

server = Server(
    APP_NAME,
    version="1.0.0",
    capabilities={
        "tools": {"listChanged": True},
        "resources": {"subscribe": True, "listChanged": True},
        "prompts": {"listChanged": True},
    }
)

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
DOCKER_COMPOSE_FILE = str(DOCKER_DIR / "docker-compose.yml")


def run_docker_command(args: list[str]) -> tuple[bool, str]:
    """Run docker compose command and return success status and output."""
    # Try with sg docker first (when not in docker group directly)
    cmds_to_try = [
        ["sg", "docker", "-c", " ".join(["docker", "compose", "-f", DOCKER_COMPOSE_FILE] + args)],
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


def run_docker_direct(args: list[str]) -> tuple[bool, str]:
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


async def http_get(url: str, timeout: float = 5.0) -> tuple[bool, Any]:
    """Make HTTP GET request."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True, response.json() if "json" in response.headers.get("content-type", "") else response.text
            return False, f"HTTP {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return False, str(e)


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="docker_status",
            description="Check status of all Docker containers for the AI Learning System",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="docker_logs",
            description="Get logs from a specific Docker service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name (app, db, redis, minio, ollama, worker, etc.)",
                        "enum": ["app", "db", "redis", "minio", "ollama", "worker", "beat", "nginx", "prometheus", "grafana"]
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of lines to fetch (default: 50)",
                        "default": 50
                    }
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="docker_restart",
            description="Restart a specific Docker service",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service name to restart",
                        "enum": ["app", "db", "redis", "minio", "ollama", "worker", "beat", "nginx"]
                    }
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="health_check",
            description="Check health status of all services (API, database, Redis, MinIO, Ollama)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="api_docs",
            description="Get OpenAPI documentation info and available endpoints",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="read_config",
            description="Read project configuration (.env file)",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="project_status",
            description="Get overall project status including implementation progress",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="dependencies_check",
            description="Check status of Python dependencies",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="ollama_status",
            description="Check Ollama status and available models",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="pull_ollama_model",
            description="Pull an AI model to Ollama",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {
                        "type": "string",
                        "description": "Model name (e.g., llama3.1, llama3.2:1b, mistral)",
                        "default": "llama3.1"
                    }
                },
                "required": ["model"]
            }
        ),
        Tool(
            name="run_tests",
            description="Run backend pytest tests inside Docker container",
            inputSchema={
                "type": "object",
                "properties": {
                    "scope": {
                        "type": "string",
                        "description": "Test scope: unit, integration, or all",
                        "enum": ["unit", "integration", "all"],
                        "default": "all"
                    },
                    "verbose": {
                        "type": "boolean",
                        "description": "Enable verbose output",
                        "default": False
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="run_lint",
            description="Run flake8 linter on backend code inside Docker container",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="api_test",
            description="Test a specific API endpoint",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {
                        "type": "string",
                        "description": "HTTP method",
                        "enum": ["GET", "POST", "PUT", "DELETE"],
                        "default": "GET"
                    },
                    "path": {
                        "type": "string",
                        "description": "API path, e.g. /health"
                    },
                    "body": {
                        "type": "object",
                        "description": "Request body (optional)"
                    },
                    "token": {
                        "type": "string",
                        "description": "Bearer token for Authorization header (optional)"
                    }
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="celery_inspect",
            description="Check Celery worker status, active tasks and queues",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="error_search",
            description="Search for errors across all container logs",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Keyword to search for (default: ERROR)",
                        "default": "ERROR"
                    },
                    "lines": {
                        "type": "integer",
                        "description": "Number of recent log lines to scan per service (default: 100)",
                        "default": 100
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="db_query",
            description="Execute a read-only SQL query on PostgreSQL (SELECT/SHOW/EXPLAIN only)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "SQL query (must start with SELECT, SHOW, or EXPLAIN)"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="redis_inspect",
            description="Inspect Redis state: memory, queue lengths, key count",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="performance_check",
            description="Check container CPU/memory resource usage via docker stats",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="minio_inspect",
            description="Inspect MinIO storage health and bucket contents",
            inputSchema={"type": "object", "properties": {}, "required": []}
        ),
        Tool(
            name="service_diagnosis",
            description="Full diagnosis of a specific service: health + logs + restart count",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "Service to diagnose",
                        "enum": ["app", "worker", "beat", "db", "redis", "minio", "nginx"]
                    }
                },
                "required": ["service"]
            }
        ),
        Tool(
            name="run_system_tests",
            description="Run the full AI Learning System test plan: infrastructure, auth, documents, quiz, knowledge base, translation, dashboard stats, and celery checks. Reports pass/fail for each test.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Test category to run (default: all)",
                        "enum": ["all", "infrastructure", "auth", "documents", "quiz", "knowledge", "translation", "dashboard", "celery"]
                    }
                },
                "required": []
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool call."""
    
    if name == "docker_status":
        success, output = run_docker_command(["ps"])
        if success:
            return [TextContent(type="text", text=f"Docker Containers Status:\n\n```\n{output}\n```")]
        return [TextContent(type="text", text=f"Error getting Docker status:\n{output}")]
    
    elif name == "docker_logs":
        service = arguments["service"]
        lines = arguments.get("lines", 50)
        success, output = run_docker_command(["logs", f"--tail={lines}", service])
        if success:
            return [TextContent(type="text", text=f"Logs for {service} (last {lines} lines):\n\n```\n{output}\n```")]
        return [TextContent(type="text", text=f"Error getting logs for {service}:\n{output}")]
    
    elif name == "docker_restart":
        service = arguments["service"]
        success, output = run_docker_command(["restart", service])
        if success:
            return [TextContent(type="text", text=f"Service {service} restarted successfully.\n\n{output}")]
        return [TextContent(type="text", text=f"Error restarting {service}:\n{output}")]
    
    elif name == "health_check":
        results = []
        services = [
            ("API", f"{API_BASE_URL}/health"),
            ("Database", f"{API_BASE_URL}/ready"),
            ("MinIO", "http://localhost:9000/minio/health/live"),
            ("Ollama", "http://localhost:11434/api/tags"),
            ("Redis", None),
        ]
        
        for service_name, url in services:
            if url:
                success, data = await http_get(url)
                if success:
                    results.append(f"✅ {service_name}: Healthy")
                else:
                    results.append(f"❌ {service_name}: {data}")
            else:
                success, output = run_docker_command(["exec", "redis", "redis-cli", "ping"])
                if success and "PONG" in output:
                    results.append(f"✅ {service_name}: Healthy (PONG)")
                else:
                    results.append(f"❌ {service_name}: Not responding")
        
        return [TextContent(type="text", text="Health Check Results:\n\n" + "\n".join(results))]
    
    elif name == "api_docs":
        success, data = await http_get(f"{API_BASE_URL}/openapi.json")
        if success:
            endpoints = []
            for path, methods in data.get("paths", {}).items():
                for method, info in methods.items():
                    summary = info.get("summary", "No description")
                    endpoints.append(f"{method.upper():6} {path:40} - {summary}")
            return [TextContent(
                type="text",
                text=f"API Documentation ({data.get('info', {}).get('title', 'Unknown')}):\n\n" +
                     f"Version: {data.get('info', {}).get('version', 'Unknown')}\n\n" +
                     "Endpoints:\n" + "\n".join(endpoints[:50]) +
                     (f"\n\n... and {len(endpoints) - 50} more" if len(endpoints) > 50 else "")
            )]
        return [TextContent(type="text", text=f"Error fetching API docs:\n{data}")]
    
    elif name == "read_config":
        env_file = DOCKER_DIR / ".env"
        if env_file.exists():
            content = env_file.read_text()
            safe_content = "\n".join(
                line if not any(k in line.lower() for k in ["password", "secret", "key", "token"]) 
                else line.split("=")[0] + "=***HIDDEN***"
                for line in content.split("\n")
            )
            return [TextContent(type="text", text=f"Configuration (.env):\n\n```\n{safe_content}\n```")]
        return [TextContent(type="text", text="No .env file found. Copy .env.example to .env first.")]
    
    elif name == "project_status":
        status_parts = []
        
        status_parts.append("PROJECT STATUS: AI Learning System")
        status_parts.append("=" * 50)
        status_parts.append(f"Project Root: {PROJECT_ROOT}")
        status_parts.append(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        status_parts.append("")
        
        missing_things_file = PROJECT_ROOT / "NEDOSTAJUCE_STVARI.md"
        if missing_things_file.exists():
            content = missing_things_file.read_text()
            lines = content.split("\n")
            phases = [l for l in lines if l.startswith("FAZA") and "IMPLEMENTACIJA" not in l]
            status_parts.append("Implementation Phases:")
            for phase in phases[:15]:
                status_parts.append(f"  {phase}")
        
        status_parts.append("")
        success, _ = run_docker_command(["ps", "-q"])
        status_parts.append(f"Docker: {'Running' if success else 'Not Available'}")
        
        return [TextContent(type="text", text="\n".join(status_parts))]
    
    elif name == "dependencies_check":
        deps_file = PROJECT_ROOT / "DEPENDENCIES_STATUS.md"
        if deps_file.exists():
            content = deps_file.read_text()
            lines = content.split("\n")[:80]
            return [TextContent(type="text", text="Dependencies Status:\n\n" + "\n".join(lines))]
        
        req_file = PROJECT_ROOT / "backend" / "requirements.txt"
        if req_file.exists():
            content = req_file.read_text()
            packages = [l for l in content.split("\n") if l and not l.startswith("#")]
            return [TextContent(type="text", text=f"Required packages ({len(packages)}):\n\n" + "\n".join(packages[:30]))]
        
        return [TextContent(type="text", text="No dependencies information found.")]
    
    elif name == "ollama_status":
        success, data = await http_get("http://localhost:11434/api/tags", timeout=10.0)
        if success:
            models = data.get("models", [])
            if models:
                model_list = [f"  - {m.get('name', 'unknown')} ({m.get('size', 'unknown size')})" for m in models]
                return [TextContent(type="text", text="Ollama Status: Running\n\nAvailable Models:\n" + "\n".join(model_list))]
            return [TextContent(type="text", text="Ollama Status: Running\n\nNo models installed. Use pull_ollama_model to download one.")]
        return [TextContent(type="text", text=f"Ollama Status: Not available\n\n{data}")]
    
    elif name == "pull_ollama_model":
        model = arguments["model"]
        return [TextContent(
            type="text",
            text=f"To pull model '{model}', run:\n\n" +
                 f"docker compose exec ollama ollama pull {model}\n\n" +
                 "This is a long-running operation. Check progress with docker_logs tool for 'ollama' service."
        )]

    elif name == "run_tests":
        scope = arguments.get("scope", "all")
        verbose = arguments.get("verbose", False)
        if scope == "all":
            test_path = "app/tests/"
        else:
            test_path = f"app/tests/{scope}/"
        flags = "-v --tb=short --no-header" if verbose else "--tb=short --no-header -q"
        try:
            result = subprocess.run(
                ["docker", "exec", "ai-learning-app", "pytest", test_path] + flags.split(),
                capture_output=True, text=True, timeout=120
            )
            output = result.stdout + result.stderr
            return [TextContent(type="text", text=f"Test results (scope={scope}):\n\n```\n{output}\n```")]
        except subprocess.TimeoutExpired:
            return [TextContent(type="text", text="Tests timed out after 120 seconds.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error running tests: {e}")]

    elif name == "run_lint":
        try:
            result = subprocess.run(
                ["docker", "exec", "ai-learning-app", "flake8", "app",
                 "--max-line-length=120", "--extend-ignore=E203,W503,E501",
                 "--exclude=app/db/migrations"],
                capture_output=True, text=True, timeout=60
            )
            output = (result.stdout + result.stderr).strip()
            if not output:
                output = "No issues found"
            return [TextContent(type="text", text=f"Lint results:\n\n```\n{output}\n```")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error running lint: {e}")]

    elif name == "api_test":
        method = arguments.get("method", "GET").upper()
        path = arguments["path"]
        body = arguments.get("body")
        token = arguments.get("token")
        url = f"{API_BASE_URL}{path}"
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        try:
            import time
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = time.monotonic()
                response = await client.request(method, url, json=body, headers=headers)
                elapsed_ms = round((time.monotonic() - start) * 1000, 1)
            try:
                resp_body = response.json()
                resp_text = json.dumps(resp_body, ensure_ascii=False, indent=2)
            except Exception:
                resp_text = response.text
            resp_text = resp_text[:500] + ("..." if len(resp_text) > 500 else "")
            return [TextContent(type="text", text=(
                f"API Test: {method} {url}\n"
                f"Status: {response.status_code}\n"
                f"Response time: {elapsed_ms}ms\n\n"
                f"Body:\n```\n{resp_text}\n```"
            ))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error calling {url}: {e}")]

    elif name == "celery_inspect":
        parts = []
        for inspect_cmd in ["active", "reserved", "stats"]:
            try:
                result = subprocess.run(
                    ["docker", "exec", "ai-learning-worker", "celery",
                     "-A", "app.workers.celery_app", "inspect", inspect_cmd],
                    capture_output=True, text=True, timeout=30
                )
                out = (result.stdout + result.stderr).strip()
                parts.append(f"=== inspect {inspect_cmd} ===\n{out}")
            except Exception as e:
                parts.append(f"=== inspect {inspect_cmd} ===\nError: {e}")
        return [TextContent(type="text", text="Celery Inspect:\n\n" + "\n\n".join(parts))]

    elif name == "error_search":
        keyword = arguments.get("keyword", "ERROR")
        lines = arguments.get("lines", 100)
        services = ["app", "worker", "beat", "db", "redis", "nginx"]
        summary_parts = []
        for svc in services:
            _, log_output = run_docker_command(["logs", f"--tail={lines}", svc])
            matches = [l for l in log_output.splitlines() if keyword.lower() in l.lower()]
            count = len(matches)
            last_three = "\n".join(matches[-3:]) if matches else "(none)"
            summary_parts.append(f"### {svc} — {count} match(es)\n{last_three}")
        return [TextContent(type="text", text=(
            f"Error search for '{keyword}' (last {lines} lines per service):\n\n" +
            "\n\n".join(summary_parts)
        ))]

    elif name == "db_query":
        query = arguments["query"].strip()
        if not query.upper().startswith(("SELECT", "SHOW", "EXPLAIN")):
            return [TextContent(type="text", text="Only SELECT/SHOW/EXPLAIN queries are allowed for safety.")]
        try:
            result = subprocess.run(
                ["docker", "exec", "ai-learning-db", "psql",
                 "-U", "ai_learning_user", "-d", "ai_learning_db",
                 "-c", query, "--no-psqlrc", "-q"],
                capture_output=True, text=True, timeout=30
            )
            output = (result.stdout + result.stderr).strip()
            return [TextContent(type="text", text=f"Query result:\n\n```\n{output}\n```")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error running query: {e}")]

    elif name == "redis_inspect":
        parts = []
        redis_cmds = [
            ("INFO server", ["docker", "exec", "ai-learning-redis", "redis-cli", "INFO", "server"]),
            ("INFO memory", ["docker", "exec", "ai-learning-redis", "redis-cli", "INFO", "memory"]),
            ("LLEN celery", ["docker", "exec", "ai-learning-redis", "redis-cli", "LLEN", "celery"]),
            ("LLEN default", ["docker", "exec", "ai-learning-redis", "redis-cli", "LLEN", "default"]),
            ("DBSIZE", ["docker", "exec", "ai-learning-redis", "redis-cli", "DBSIZE"]),
            ("KEYS blacklist:*", ["docker", "exec", "ai-learning-redis", "redis-cli", "KEYS", "blacklist:*"]),
        ]
        for label, cmd in redis_cmds:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                out = (result.stdout + result.stderr).strip()
                # For INFO, keep only relevant lines
                if label.startswith("INFO"):
                    relevant = [l for l in out.splitlines()
                                if any(k in l for k in ["redis_version", "uptime_in_seconds", "used_memory_human", "connected_clients"])]
                    out = "\n".join(relevant) if relevant else out[:300]
                parts.append(f"**{label}**: {out}")
            except Exception as e:
                parts.append(f"**{label}**: Error — {e}")
        return [TextContent(type="text", text="Redis Inspect:\n\n" + "\n".join(parts))]

    elif name == "performance_check":
        try:
            result = subprocess.run(
                ["docker", "stats", "--no-stream", "--format",
                 "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}"],
                capture_output=True, text=True, timeout=30
            )
            output = result.stdout or result.stderr
            lines = output.splitlines()[:20]
            return [TextContent(type="text", text="Container Resource Usage:\n\n```\n" + "\n".join(lines) + "\n```")]
        except Exception as e:
            return [TextContent(type="text", text=f"Error checking performance: {e}")]

    elif name == "minio_inspect":
        parts = []
        # Health check via HTTP
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get("http://localhost:9000/minio/health/live")
                parts.append(f"MinIO health: {'✅ OK' if resp.status_code == 200 else f'❌ HTTP {resp.status_code}'}")
        except Exception as e:
            parts.append(f"MinIO health: ❌ Unreachable ({e})")
        # Bucket listing fallback
        try:
            result = subprocess.run(
                ["docker", "exec", "ai-learning-minio", "sh", "-c",
                 "ls -la /data/ai-learning-uploads/ 2>/dev/null | head -20 || echo 'bucket not found'"],
                capture_output=True, text=True, timeout=15
            )
            out = (result.stdout + result.stderr).strip()
            parts.append(f"\nBucket contents:\n```\n{out}\n```")
        except Exception as e:
            parts.append(f"\nBucket listing error: {e}")
        return [TextContent(type="text", text="MinIO Inspect:\n\n" + "\n".join(parts))]

    elif name == "service_diagnosis":
        service = arguments["service"]
        container = f"ai-learning-{service}"
        report = [f"# Service Diagnosis: {service}\n"]

        # Health check
        health_url_map = {
            "app": f"{API_BASE_URL}/health",
            "db": None,
            "redis": None,
            "minio": "http://localhost:9000/minio/health/live",
        }
        if service in health_url_map and health_url_map[service]:
            ok, data = await http_get(health_url_map[service])
            report.append(f"**Health**: {'✅ OK' if ok else f'❌ {data}'}")
        elif service == "db":
            ok, out = run_docker_command(["exec", "db", "pg_isready", "-U", "ai_learning_user"])
            report.append(f"**Health**: {'✅ Ready' if ok else f'❌ {out}'}")
        elif service == "redis":
            ok, out = run_docker_command(["exec", "redis", "redis-cli", "ping"])
            report.append(f"**Health**: {'✅ PONG' if ok and 'PONG' in out else f'❌ {out}'}")

        # Docker inspect
        try:
            result = subprocess.run(
                ["docker", "inspect", container,
                 "--format", "Status: {{.State.Status}}, RestartCount: {{.RestartCount}}, StartedAt: {{.State.StartedAt}}"],
                capture_output=True, text=True, timeout=10
            )
            inspect_out = (result.stdout + result.stderr).strip()
            report.append(f"**Inspect**: {inspect_out}")
        except Exception as e:
            report.append(f"**Inspect**: Error — {e}")

        # Last 30 lines of logs
        _, log_out = run_docker_command(["logs", "--tail=30", service])
        report.append(f"\n**Last 30 log lines**:\n```\n{log_out.strip()}\n```")

        return [TextContent(type="text", text="\n".join(report))]

    elif name == "run_system_tests":
        category = arguments.get("category", "all")
        report = await _run_system_tests(category)
        return [TextContent(type="text", text=report)]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM TEST RUNNER
# ─────────────────────────────────────────────────────────────────────────────

async def _run_system_tests(category: str = "all") -> str:
    """
    Comprehensive test plan for AI Learning System.
    Returns a markdown report with pass/fail for each test.
    """
    results = []
    passed = 0
    failed = 0

    def ok(name: str, detail: str = ""):
        nonlocal passed
        passed += 1
        results.append(f"✅ **{name}**" + (f" — {detail}" if detail else ""))

    def fail(name: str, detail: str = ""):
        nonlocal failed
        failed += 1
        results.append(f"❌ **{name}**" + (f" — {detail}" if detail else ""))

    def section(title: str):
        results.append(f"\n### {title}")

    # ── 1. INFRASTRUCTURE ────────────────────────────────────────────────────
    if category in ("all", "infrastructure"):
        section("🏗️ Infrastructure")

        expected_containers = [
            "ai-learning-app", "ai-learning-worker", "ai-learning-db",
            "ai-learning-nginx", "ai-learning-beat", "ai-learning-redis",
            "ai-learning-minio"
        ]
        try:
            ok_docker, running = run_docker_direct(["ps", "--filter", "name=ai-learning"])
            if not ok_docker:
                fail("Docker access", running)
            else:
                for c in expected_containers:
                    if c in running:
                        ok(f"Container {c}")
                    else:
                        fail(f"Container {c}", "not running or unhealthy")
        except Exception as e:
            fail("Docker ps", str(e))

        # Redis ping
        ok_r, out_r = run_docker_direct(["exec", "ai-learning-redis", "redis-cli", "ping"])
        if ok_r and "PONG" in out_r:
            ok("Redis ping")
        else:
            fail("Redis ping", out_r[:50])

        # DB ready
        ok_db, out_db = run_docker_direct(["exec", "ai-learning-db", "pg_isready", "-U", "ai_learning_user"])
        if ok_db:
            ok("PostgreSQL ready")
        else:
            fail("PostgreSQL ready", out_db[:50])

        # API health
        ok2, data2 = await http_get("http://localhost/api/v1/health")
        if ok2 and isinstance(data2, dict) and data2.get("status") == "healthy":
            ok("API /health", f"version={data2.get('version','?')}")
        else:
            fail("API /health", str(data2)[:100])

        # Nginx serving frontend
        ok3, html = await http_get("http://localhost/")
        if ok3 and "<!DOCTYPE html>" in str(html):
            ok("Nginx serves frontend")
        else:
            fail("Nginx serves frontend", str(html)[:100])

        # [BUG-FIX-2026-03-01] index.html must NOT be cached — stale cache causes 404+no-sidebar
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get("http://localhost/")
                cc = r.headers.get("cache-control", "")
                if "no-cache" in cc or "no-store" in cc:
                    ok("index.html has no-cache header")
                else:
                    fail("index.html has no-cache header", f"Cache-Control: '{cc}' — old JS bundle will be cached causing 404 on SPA routes")
        except Exception as e:
            fail("index.html cache headers", repr(e))

        # [BUG-FIX-2026-03-01] /review SPA route must resolve (not 404)
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get("http://localhost/review")
                if r.status_code == 200 and "<!DOCTYPE html>" in r.text:
                    ok("SPA /review route resolves to index.html")
                else:
                    fail("SPA /review route resolves to index.html", f"HTTP {r.status_code}")
        except Exception as e:
            fail("SPA /review route resolves to index.html", repr(e))

    # ── 2. AUTHENTICATION ─────────────────────────────────────────────────────
    token = None
    if category in ("all", "auth"):
        section("🔐 Authentication")
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Login
                r = await client.post(
                    "http://localhost/api/v1/auth/login",
                    data={"username": "testuser@test.com", "password": "Test1234!"}
                )
                if r.status_code == 200:
                    token = r.json().get("access_token")
                    ok("Login (testuser@test.com)", f"token_len={len(token or '')}")
                else:
                    fail("Login", f"HTTP {r.status_code}: {r.text[:100]}")

                # Get current user
                if token:
                    r2 = await client.get(
                        "http://localhost/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    if r2.status_code == 200:
                        user = r2.json()
                        ok("GET /auth/me", f"email={user.get('email','?')}")
                    else:
                        fail("GET /auth/me", f"HTTP {r2.status_code}")

                # Invalid login should fail
                r3 = await client.post(
                    "http://localhost/api/v1/auth/login",
                    data={"username": "wrong@wrong.com", "password": "wrong"}
                )
                if r3.status_code in (401, 400, 422):
                    ok("Login rejects invalid credentials", f"HTTP {r3.status_code}")
                else:
                    fail("Login rejects invalid credentials", f"Got HTTP {r3.status_code}")
        except Exception as e:
            fail("Auth tests", str(e))
    else:
        # Get token for other tests
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    "http://localhost/api/v1/auth/login",
                    data={"username": "testuser@test.com", "password": "Test1234!"}
                )
                token = r.json().get("access_token") if r.status_code == 200 else None
        except Exception:
            pass

    # ── 3. DOCUMENTS ──────────────────────────────────────────────────────────
    if category in ("all", "documents"):
        section("📄 Documents")
        if not token:
            fail("Document tests", "No auth token — login failed")
        else:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    hdrs = {"Authorization": f"Bearer {token}"}

                    # List documents
                    r = await client.get("http://localhost/api/v1/documents/", headers=hdrs)
                    if r.status_code == 200:
                        docs = r.json()
                        count = docs.get("total", 0)
                        ok("GET /documents/", f"total={count}")

                        # Check translated_chunks field
                        items = docs.get("items", [])
                        if items:
                            has_field = "translated_chunks" in items[0]
                            if has_field:
                                ok("Document has translated_chunks field")
                            else:
                                fail("Document has translated_chunks field", "field missing from response")
                    else:
                        fail("GET /documents/", f"HTTP {r.status_code}")

                    # Check chunks endpoint
                    items = docs.get("items", []) if r.status_code == 200 else []
                    completed_docs = [d for d in items if d.get("status") == "completed"]
                    if completed_docs:
                        doc_id = completed_docs[0]["id"]
                        rc = await client.get(f"http://localhost/api/v1/documents/{doc_id}/chunks", headers=hdrs)
                        if rc.status_code == 200:
                            chunks_data = rc.json()
                            chunk_count = len(chunks_data) if isinstance(chunks_data, list) else chunks_data.get("total", 0)
                            ok(f"GET /documents/{{id}}/chunks", f"chunks={chunk_count}")
                        else:
                            fail("GET /documents/{id}/chunks", f"HTTP {rc.status_code}")

                    # Translation stats
                    translated_docs = [d for d in items if (d.get("translated_chunks") or 0) > 0]
                    ok("Translated documents count", f"{len(translated_docs)} of {len(items)} have translations")
            except Exception as e:
                fail("Document tests", str(e))

    # ── 4. QUIZ ───────────────────────────────────────────────────────────────
    if category in ("all", "quiz"):
        section("🎯 Quiz")
        if not token:
            fail("Quiz tests", "No auth token")
        else:
            try:
                async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                    hdrs = {"Authorization": f"Bearer {token}"}
                    r = await client.get("http://localhost/api/v1/quizzes/", headers=hdrs)
                    if r.status_code == 200:
                        quiz_data = r.json()
                        total = quiz_data.get("total", 0)
                        ok("GET /quizzes/", f"total={total}")

                        items = quiz_data.get("items", [])
                        # Find a quiz with questions
                        for quiz in items:
                            qid = quiz.get("id")
                            rq = await client.get(f"http://localhost/api/v1/quizzes/{qid}", headers=hdrs)
                            if rq.status_code == 200:
                                qd = rq.json()
                                questions = qd.get("questions", [])
                                if questions:
                                    q = questions[0]
                                    has_answer = "correct_answer" in q and q.get("correct_answer") is not None
                                    if has_answer:
                                        ok("Quiz question has correct_answer", f"quiz={qid[:8]}...")
                                    else:
                                        fail("Quiz question has correct_answer", "field missing or null")
                                    has_exp = "explanation" in q
                                    ok("Quiz question has explanation field") if has_exp else fail("Quiz question has explanation field")
                                    break
                    else:
                        fail("GET /quizzes/", f"HTTP {r.status_code}")
            except Exception as e:
                fail("Quiz tests", repr(e))

    # ── 5. KNOWLEDGE BASE ─────────────────────────────────────────────────────
    if category in ("all", "knowledge"):
        section("🧠 Knowledge Base")
        if not token:
            fail("Knowledge tests", "No auth token")
        else:
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    hdrs = {"Authorization": f"Bearer {token}"}

                    # Stats
                    r = await client.get("http://localhost/api/v1/knowledge/stats", headers=hdrs)
                    if r.status_code == 200:
                        stats = r.json()
                        ok("GET /knowledge/stats", f"sources={stats.get('total_sources',0)}, indexed={stats.get('indexed_sources',0)}")
                    else:
                        fail("GET /knowledge/stats", f"HTTP {r.status_code}")

                    # URL ingest endpoint (just check it returns 200, not 500)
                    r2 = await client.post(
                        "http://localhost/api/v1/knowledge/ingest/url",
                        headers=hdrs,
                        json={"url": "https://example.com", "name": "Test - MCP health check", "recursive": False}
                    )
                    if r2.status_code == 200:
                        ok("POST /knowledge/ingest/url", f"status={r2.json().get('status','?')}")
                    else:
                        fail("POST /knowledge/ingest/url", f"HTTP {r2.status_code}: {r2.text[:100]}")

                # RAG query uses a separate client with longer timeout (Ollama can be slow)
                try:
                    async with httpx.AsyncClient(timeout=60) as slow_client:
                        r3 = await slow_client.post(
                            "http://localhost/api/v1/knowledge/query",
                            headers={"Authorization": f"Bearer {token}"},
                            json={"query": "test query for health check", "top_k": 3}
                        )
                        if r3.status_code == 200:
                            qdata = r3.json()
                            ok("POST /knowledge/query", f"answer_len={len(qdata.get('answer',''))}")
                        else:
                            fail("POST /knowledge/query", f"HTTP {r3.status_code}")
                except Exception as eq:
                    fail("POST /knowledge/query", repr(eq))
            except Exception as e:
                fail("Knowledge tests", repr(e))

    # ── 6. TRANSLATION ────────────────────────────────────────────────────────
    if category in ("all", "translation"):
        section("🌐 Translation")
        if not token:
            fail("Translation tests", "No auth token")
        else:
            try:
                async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                    hdrs = {"Authorization": f"Bearer {token}"}

                    r = await client.get("http://localhost/api/v1/documents/translation/providers", headers=hdrs)
                    if r.status_code == 200:
                        providers = r.json()
                        ok("GET /translation/providers", f"providers={list(providers.keys()) if isinstance(providers, dict) else providers}")
                    else:
                        fail("GET /translation/providers", f"HTTP {r.status_code}")

                    # Check that completed translated docs have translated_chunks > 0
                    r2 = await client.get("http://localhost/api/v1/documents/?limit=20", headers=hdrs)
                    if r2.status_code == 200:
                        items = r2.json().get("items", [])
                        translated = [d for d in items if (d.get("translated_chunks") or 0) > 0]
                        ok("Translated docs visible in list", f"{len(translated)} documents with translations")

                    # [BUG-FIX-2026-03-01] /review route — frontend must serve TranslationsPage
                    r3 = await client.get("http://localhost/review")
                    if r3.status_code == 200 and "<!DOCTYPE html>" in r3.text:
                        ok("Frontend /review route served")
                    else:
                        fail("Frontend /review route served", f"HTTP {r3.status_code}")

                    # [BUG-FIX-2026-03-01] Translated docs must be visible via /review
                    # (same data as document list — translated_chunks > 0)
                    if r2.status_code == 200:
                        items = r2.json().get("items", [])
                        translated_with_chunks = [d for d in items if (d.get("translated_chunks") or 0) > 0]
                        if translated_with_chunks:
                            ok("Translated docs accessible for /review", f"{len(translated_with_chunks)} docs with translated_chunks>0")
                        else:
                            fail("Translated docs accessible for /review", "no documents with translated_chunks>0")
            except Exception as e:
                fail("Translation tests", repr(e))

    # ── 6b. DASHBOARD STATS ───────────────────────────────────────────────────
    if category in ("all", "dashboard"):
        section("📊 Dashboard Stats")
        if not token:
            fail("Dashboard stats", "No auth token")
        else:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    hdrs = {"Authorization": f"Bearer {token}"}

                    r = await client.get("http://localhost/api/v1/users/me/stats", headers=hdrs)
                    if r.status_code != 200:
                        fail("GET /users/me/stats", f"HTTP {r.status_code}")
                    else:
                        s = r.json()
                        ok("GET /users/me/stats", f"HTTP 200")

                        # [BUG-FIX-2026-03-01] Stats must not return all zeros when user has documents
                        required_fields = ["total_documents", "total_chunks", "translated_chunks",
                                           "total_quizzes_taken", "study_streak"]
                        missing = [f for f in required_fields if f not in s]
                        if missing:
                            fail("UserStats has required fields", f"missing: {missing}")
                        else:
                            ok("UserStats has required fields", f"fields={required_fields}")

                        # total_documents must reflect real DB data (not hardcoded 0)
                        if s.get("total_documents", 0) > 0:
                            ok("Dashboard total_documents is real", f"total={s['total_documents']}")
                        else:
                            fail("Dashboard total_documents is real", "returned 0 — may be hardcoded placeholder")

                        # translated_chunks field exists and is integer
                        if isinstance(s.get("translated_chunks"), int):
                            ok("Dashboard translated_chunks field", f"value={s['translated_chunks']}")
                        else:
                            fail("Dashboard translated_chunks field", "missing or wrong type")

                        # study_streak field exists (frontend uses this key)
                        if "study_streak" in s:
                            ok("Dashboard study_streak field present")
                        else:
                            fail("Dashboard study_streak field present", "key missing — frontend shows 0")
            except Exception as e:
                fail("Dashboard stats", repr(e))

    # ── 7. CELERY WORKER ──────────────────────────────────────────────────────
    if category in ("all", "celery"):
        section("⚙️ Celery Worker")
        # Write a temp script to avoid shell quoting issues with complex Python code
        import tempfile, os
        celery_script = (
            "import sys; sys.path.insert(0, '/app')\n"
            "from app.workers.celery_app import celery_app\n"
            "r = celery_app.control.inspect(timeout=3).ping()\n"
            "print('OK' if r else 'NO_WORKERS')\n"
        )
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(celery_script)
            tmp_path = f.name
        try:
            # Copy script into container and run it
            ok_cp, _ = run_docker_direct(["cp", tmp_path, f"ai-learning-app:/tmp/celery_check.py"])
            if ok_cp:
                ok_ping, out_ping = run_docker_direct(["exec", "ai-learning-app", "python3", "/tmp/celery_check.py"])
            else:
                ok_ping, out_ping = False, "Failed to copy script"
        finally:
            os.unlink(tmp_path)
        out_ping = out_ping.strip()
        if "OK" in out_ping:
            ok("Celery worker ping")
        else:
            fail("Celery worker ping", out_ping[:100])

        # Check worker logs for recent errors
        ok_logs, logs = run_docker_direct(["logs", "ai-learning-worker", "--tail=20"])
        if ok_logs:
            error_count = logs.lower().count("error")
            if error_count == 0:
                ok("Worker recent logs (no errors)")
            else:
                fail("Worker recent logs", f"{error_count} errors in last 20 lines")
        else:
            fail("Worker logs check", logs[:50])

    # ── SUMMARY ───────────────────────────────────────────────────────────────
    total = passed + failed
    score = f"{passed}/{total}"
    status_emoji = "🟢" if failed == 0 else ("🟡" if failed <= 2 else "🔴")

    header = [
        f"# {status_emoji} AI Learning System — Test Report",
        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Category:** {category}",
        f"**Score:** {score} tests passed ({passed * 100 // total if total else 0}%)",
        ""
    ]

    return "\n".join(header + results + [
        "",
        f"---",
        f"**Total: {passed} passed, {failed} failed**"
    ])


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available MCP resources."""
    resources = [
        Resource(
            uri="file:///project/README.md",
            name="Project README",
            mimeType="text/markdown",
            description="Project documentation and overview"
        ),
        Resource(
            uri="file:///project/DEPENDENCIES_STATUS.md",
            name="Dependencies Status",
            mimeType="text/markdown",
            description="Status of all Python dependencies"
        ),
        Resource(
            uri="file:///project/NEDOSTAJUCE_STVARI.md",
            name="Missing Features",
            mimeType="text/markdown",
            description="List of features not yet implemented"
        ),
        Resource(
            uri="file:///project/INSTALLATION_GUIDE.md",
            name="Installation Guide",
            mimeType="text/markdown",
            description="Step-by-step installation instructions"
        ),
    ]
    
    logs_dir = PROJECT_ROOT / "logs"
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            resources.append(Resource(
                uri=f"file:///logs/{log_file.name}",
                name=f"Log: {log_file.name}",
                mimeType="text/plain",
                description=f"Application log file"
            ))
    
    return resources


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    if uri.startswith("file:///project/"):
        filename = uri.replace("file:///project/", "")
        filepath = PROJECT_ROOT / filename
        if filepath.exists():
            return filepath.read_text()
        return f"File not found: {filename}"
    
    elif uri.startswith("file:///logs/"):
        filename = uri.replace("file:///logs/", "")
        filepath = PROJECT_ROOT / "logs" / filename
        if filepath.exists():
            return filepath.read_text()
        return f"Log file not found: {filename}"
    
    return f"Unknown resource URI: {uri}"


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available MCP prompts."""
    return [
        Prompt(
            name="system-diagnosis",
            description="Generate a comprehensive system diagnosis report",
            arguments=[
                {"name": "service", "description": "Service to diagnose (app, worker, db, redis, minio, nginx)", "required": False}
            ]
        ),
        Prompt(
            name="docker-troubleshoot",
            description="Troubleshoot Docker container issues and get recommendations",
            arguments=[
                {"name": "container", "description": "Container name to troubleshoot", "required": False}
            ]
        ),
        Prompt(
            name="project-health-check",
            description="Perform a complete project health check with recommendations",
            arguments=[]
        ),
        Prompt(
            name="error-analysis",
            description="Analyze errors in container logs and suggest fixes",
            arguments=[
                {"name": "keyword", "description": "Error keyword to search (default: ERROR)", "required": False},
                {"name": "lines", "description": "Number of log lines to analyze (default: 100)", "required": False}
            ]
        ),
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any] | None = None) -> PromptMessage:
    """Get a prompt template with arguments."""
    arguments = arguments or {}
    
    if name == "system-diagnosis":
        service = arguments.get("service", "all")
        result = await _get_system_diagnosis(service)
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=result)
        )
    
    elif name == "docker-troubleshoot":
        container = arguments.get("container")
        result = await _get_docker_troubleshoot(container)
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=result)
        )
    
    elif name == "project-health-check":
        result = await _get_project_health_check()
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=result)
        )
    
    elif name == "error-analysis":
        keyword = arguments.get("keyword", "ERROR")
        lines = arguments.get("lines", 100)
        result = await _get_error_analysis(keyword, lines)
        return PromptMessage(
            role="user",
            content=TextContent(type="text", text=result)
        )
    
    raise ValueError(f"Unknown prompt: {name}")


async def _get_system_diagnosis(service: str) -> str:
    """Generate system diagnosis prompt content."""
    return f"""Please diagnose the AI Learning System service: {service}

Use the following MCP tools to gather information:
1. Use `docker_status` to check container status
2. Use `service_diagnosis` with service="{service}" for detailed diagnosis
3. Use `health_check` to verify all services
4. Use `performance_check` to check resource usage

After gathering data, provide:
- Current status summary
- Any issues found
- Recommended actions to resolve issues"""


async def _get_docker_troubleshoot(container: str | None) -> str:
    """Generate Docker troubleshooting prompt content."""
    if container:
        return f"""Please troubleshoot Docker container: {container}

Use these MCP tools:
1. Use `docker_status` to check overall container status
2. Use `docker_logs` with service="{container}" to view recent logs
3. Use `docker_restart` if needed to restart the service

Analyze the logs and provide:
- Root cause of any issues
- Step-by-step troubleshooting guide
- Prevention recommendations"""
    else:
        return """Please troubleshoot the Docker environment.

Use `docker_status` to list all containers, then for any unhealthy containers:
1. Check logs with `docker_logs`
2. Check resource usage with `performance_check`
3. Restart if necessary with `docker_restart`

Provide a comprehensive troubleshooting report."""


async def _get_project_health_check() -> str:
    """Generate project health check prompt content."""
    return """Please perform a comprehensive health check of the AI Learning System.

Run the following checks in order:
1. `run_system_tests` with category="all" - Full system test suite
2. `health_check` - API and service health
3. `performance_check` - Resource usage
4. `dependencies_check` - Dependency status

Then provide a health report with:
- Overall system health score (0-100%)
- List of healthy vs unhealthy components
- Top 3 priority issues to fix
- Recommended next steps"""


async def _get_error_analysis(keyword: str, lines: int) -> str:
    """Generate error analysis prompt content."""
    return f"""Please analyze errors in the AI Learning System.

Search for errors using `error_search` tool:
- keyword: "{keyword}"
- lines: {lines}

For each error found:
1. Identify the service where it occurred
2. Analyze the error pattern
3. Suggest a fix

Provide a summary including:
- Total number of errors by service
- Most common error types
- Critical issues requiring immediate attention
- Recommended fixes for each issue"""


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
