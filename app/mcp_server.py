# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/mcp_server.py
# PURPOSE: Exposes the slang generation system as MCP tools so Claude Desktop
#          and any MCP-compatible AI assistant can call them directly.
#
# THREE TOOLS:
#   - get_daily_slangs    → generates 10 fresh slangs and returns them
#   - generate_daily_pdf  → generates PDF, returns file path (local only)
#   - get_previous_slangs → all words from past days (local only)
#
# IMPORTANT — WHY WE BYPASS THE LANGGRAPH GRAPH HERE:
#   The graph's final node (display_slangs) writes Rich-formatted text to stdout.
#   MCP uses stdin/stdout as its transport protocol — any non-JSON bytes on stdout
#   corrupt the MCP communication stream. So we call the underlying functions
#   directly and never touch the display layer.
#
# CLOUD NOTE:
#   When running on a read-only filesystem (e.g. Prefect Horizon), file writes
#   are skipped gracefully. get_daily_slangs() always generates fresh and returns
#   directly without attempting to cache to disk.
# ──────────────────────────────────────────────────────────────────────────────

import sys
import os
from pathlib import Path

# Ensure we always run from the project root so relative paths like
# outputs/json/ resolve correctly, regardless of how this file is launched.
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)

from dotenv import load_dotenv

# Load .env before any module that reads GOOGLE_API_KEY
load_dotenv()

from fastmcp import FastMCP

from app.rag.retriever import get_previous_words
from app.utils.file_handler import today_slangs_exist, load_daily_slangs, save_daily_slangs
from app.ui.pdf_generator import generate_pdf


mcp = FastMCP("Daily Slang Matrix")


@mcp.tool()
def get_daily_slangs() -> list[dict]:
    """
    Returns today's 10 slang words with meaning, Banglish translation, tone, and example.
    Generates fresh slangs via Gemini on every call.
    """
    # Lazy import — slang_agent pulls in LangChain/Gemini; only load when needed
    from app.agent.slang_agent import generate_slangs

    previous = get_previous_words()
    slangs = generate_slangs(previous)

    # Try to cache to disk — silently skip if filesystem is read-only (e.g. Horizon)
    try:
        save_daily_slangs(slangs)
    except OSError:
        pass

    return [s.model_dump() for s in slangs]


@mcp.tool()
def generate_daily_pdf() -> str:
    """
    Generates a PDF of today's slangs and returns the file path.
    Only works in environments with a writable filesystem.
    """
    from app.agent.slang_agent import generate_slangs

    previous = get_previous_words()
    slangs = generate_slangs(previous)

    try:
        save_daily_slangs(slangs)
    except OSError:
        pass

    path = generate_pdf(slangs)
    return str(path)


@mcp.tool()
def get_previous_slangs() -> list[str]:
    """
    Returns all slang words generated on previous days.
    Useful for checking history or avoiding repetition.
    """
    return get_previous_words()


if __name__ == "__main__":
    mcp.run()
