# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/mcp_server.py
# PURPOSE: Exposes the slang system as MCP tools by calling the FastAPI server
#          over HTTP. The MCP server is a thin client — all business logic,
#          file system access, and LLM calls live in the API layer.
#
# WHY HTTP INSTEAD OF DIRECT FUNCTION CALLS:
#   The previous approach imported Python functions directly, which caused
#   issues on cloud platforms (read-only filesystem, env var timing, heavy
#   imports). Calling the FastAPI layer over HTTP is simpler, more reliable,
#   and works identically whether the MCP server runs locally or on Horizon.
#
# CONFIGURATION:
#   Set API_URL in the environment to point at your FastAPI server.
#   Default: http://localhost:8000 (Docker Compose api service)
#
# THREE TOOLS:
#   - get_daily_slangs    → GET /generate
#   - generate_daily_pdf  → GET /generate (returns slangs; PDF is server-side)
#   - get_previous_slangs → GET /previous-words
# ──────────────────────────────────────────────────────────────────────────────

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

import httpx
from fastmcp import FastMCP


mcp = FastMCP("Daily Slang Matrix")

# Point this at wherever your FastAPI server is running.
# Local Docker: http://localhost:8000
# Remote VPS:   https://your-domain.com
API_URL = os.getenv("API_URL", "http://localhost:8000")


@mcp.tool()
def get_daily_slangs() -> list[dict]:
    """
    Returns today's 10 slang words with meaning, Banglish translation, tone, and example.
    Calls the FastAPI /generate endpoint which handles caching and LLM generation.
    """
    response = httpx.get(f"{API_URL}/generate", timeout=60)
    response.raise_for_status()
    return response.json()["slangs"]


@mcp.tool()
def generate_daily_pdf() -> str:
    """
    Generates today's slangs and saves a PDF on the API server.
    Returns the saved file path.
    """
    response = httpx.get(f"{API_URL}/generate", timeout=60)
    response.raise_for_status()
    return response.json().get("saved_to", "PDF generated on server")


@mcp.tool()
def get_previous_slangs() -> list[str]:
    """
    Returns all slang words generated on previous days.
    Useful for checking history or avoiding repetition.
    """
    response = httpx.get(f"{API_URL}/previous-words", timeout=10)
    response.raise_for_status()
    return response.json()["words"]


if __name__ == "__main__":
    mcp.run()
