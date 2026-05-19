# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/api/routes.py
# PURPOSE: Defines all HTTP endpoints for the FastAPI server.
#
# ROUTES:
#   GET /          → health check
#   GET /today     → return today's slangs from cache (404 if not generated yet)
#   GET /generate  → call Gemini, generate fresh slangs, save and return them
#   GET /history   → list all past JSON output filenames
#
# NOTE — WHY /generate BYPASSES THE GRAPH:
#   Same reason as mcp_server.py — the graph's display node writes Rich text to
#   stdout which is inappropriate in an HTTP context. We call the agent functions
#   directly and return the data as JSON instead.
#
# HOW IT CONNECTS:
#   → app/api/app.py          mounts this router on the FastAPI instance
#   → app/agent/slang_agent.py called lazily in /generate to avoid slow startup
#   → app/utils/file_handler.py handles cache read/write
# ──────────────────────────────────────────────────────────────────────────────

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.rag.retriever import get_previous_words
from app.utils.file_handler import today_slangs_exist, load_daily_slangs, save_daily_slangs


router = APIRouter()


@router.get("/")
def home():
    return {"message": "Daily Slang Matrix"}


@router.get("/today")
def today_slangs():
    # Return 404 instead of an empty response so callers know to hit /generate first
    if not today_slangs_exist():
        raise HTTPException(status_code=404, detail="No slangs generated today yet. Call /generate first.")
    slangs = load_daily_slangs()
    return {"count": len(slangs), "slangs": [s.model_dump() for s in slangs]}


@router.get("/generate")
def generate_slangs():
    # Lazy import — keeps server startup fast; LangChain/Gemini only loaded on first call
    from app.agent.slang_agent import generate_slangs as run_generation
    previous = get_previous_words()
    slangs = run_generation(previous)
    saved_path = save_daily_slangs(slangs)
    return {
        "message": "Generated successfully",
        "saved_to": str(saved_path),
        "slangs": [s.model_dump() for s in slangs],
    }


@router.get("/history")
def get_history():
    output_dir = Path("outputs/json")
    if not output_dir.exists():
        return {"history": []}
    # Sort so newest file appears last
    files = sorted(output_dir.glob("*.json"))
    return {"history": [file.name for file in files]}
