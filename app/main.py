# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/main.py
# PURPOSE: The entry point of the entire application.
#          When you run `uv run python -m app.main`, execution starts here.
#
# WHAT IT DOES:
#   1. Fixes the Windows terminal encoding so Bengali text and emojis display
#      correctly (Windows defaults to cp1252 which can't handle Unicode).
#   2. Imports the compiled LangGraph from app/agent/graph.py.
#   3. Calls graph.invoke({}) which kicks off the full pipeline:
#      check cache → (generate + save) or skip → display in terminal.
#
# HOW IT CONNECTS:
#   → Imports `graph` from app/agent/graph.py
#   → graph.py contains the full node pipeline (check_cache, generate, save, display)
#   → This file is the only file you need to run the app
# ──────────────────────────────────────────────────────────────────────────────

import sys

# Must be called BEFORE any print or Rich output.
# Without this, Bengali characters crash on Windows with a UnicodeEncodeError.
sys.stdout.reconfigure(encoding="utf-8")

from app.agent.graph import graph


def main():
    # Start the LangGraph pipeline with an empty initial state.
    # LangGraph will fill the state as it moves through each node.
    graph.invoke({})


if __name__ == "__main__":
    main()
