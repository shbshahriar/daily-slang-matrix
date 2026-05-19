# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/mcp_server.py
# PURPOSE: Exposes the slang generation system as MCP tools so Claude Desktop
#          and any MCP-compatible AI assistant can call them directly.
#
# THREE TOOLS:
#   - get_daily_slangs    → today's 10 slangs, generates if not yet created
#   - generate_daily_pdf  → creates today's PDF, returns the file path
#   - get_previous_slangs → all words generated on previous days
#
# IMPORTANT — WHY WE BYPASS THE LANGGRAPH GRAPH HERE:
#   The graph's final node (display_slangs) writes Rich-formatted text to stdout.
#   MCP uses stdin/stdout as its transport protocol — any non-JSON bytes on stdout
#   corrupt the MCP communication stream. So we call the underlying functions
#   directly and never touch the display layer.
#
# HOW TO REGISTER WITH CLAUDE DESKTOP:
#   Add to claude_desktop_config.json:
#   {
#     "mcpServers": {
#       "daily-slang": {
#         "command": "uv",
#         "args": ["run", "python", "-m", "app.mcp_server"],
#         "cwd": "/path/to/daily-slang-matrix",
#         "env": { "GOOGLE_API_KEY": "your-key" }
#       }
#     }
#   }
# ──────────────────────────────────────────────────────────────────────────────

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
    Generates them via Gemini if today's batch hasn't been created yet.
    """
    if not today_slangs_exist():
        # Lazy import — slang_agent pulls in LangChain/Gemini; only load when needed
        from app.agent.slang_agent import generate_slangs
        previous = get_previous_words()
        slangs = generate_slangs(previous)
        save_daily_slangs(slangs)

    return [s.model_dump() for s in load_daily_slangs()]


@mcp.tool()
def generate_daily_pdf() -> str:
    """
    Generates a PDF of today's slangs and returns the file path.
    Triggers slang generation first if today's batch doesn't exist yet.
    """
    if not today_slangs_exist():
        from app.agent.slang_agent import generate_slangs
        previous = get_previous_words()
        slangs = generate_slangs(previous)
        save_daily_slangs(slangs)

    slangs = load_daily_slangs()
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
