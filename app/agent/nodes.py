# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/agent/nodes.py
# PURPOSE: Every step of the LangGraph pipeline as a function.
#          Each function receives the current state, does one job,
#          and returns a dict to update the state for the next step.
#
# FULL PIPELINE FLOW:
#
#   check_cache
#        │
#        ├── cache HIT  ──────────────────────────────────► display_slangs ──► END
#        │                                                       ▲
#        └── cache MISS ──► retrieve ──► generate_slangs ──► save_slangs ──┘
#
# NODE RESPONSIBILITIES:
#   1. check_cache_node    → Is today's file already saved? Yes = skip LLM entirely.
#   2. retrieve_node       → Scan all past output files, collect already-used words.
#   3. generate_slangs_node→ Call Gemini with history context, get 10 new slangs.
#   4. save_slangs_node    → Save new slangs to outputs/json/YYYY-MM-DD.json.
#   5. display_slangs_node → Print styled panels in the terminal.
#
# HOW IT CONNECTS:
#   → graph.py  registers these functions and defines their execution order
#   → state.py  defines SlangState — the shared data passed between nodes
# ──────────────────────────────────────────────────────────────────────────────

from app.agent.state import SlangState
from app.agent.slang_agent import generate_slangs
from app.rag.retriever import get_previous_words
from app.utils.file_handler import today_slangs_exist, load_daily_slangs, save_daily_slangs
from app.ui.terminal_ui import display_slangs
from app.ui.pdf_generator import generate_pdf


# STEP 1 — Check if today's slangs are already saved on disk.
# If yes  → load them and set cache_hit = True  (skip retrieve + LLM entirely)
# If no   → set cache_hit = False               (proceed to retrieve → generate)
def check_cache_node(state: SlangState):
    if today_slangs_exist():
        return {"cache_hit": True, "generated_slangs": load_daily_slangs()}
    return {"cache_hit": False}


# STEP 2 — Retrieve all slang words generated on previous days.
# Scans every file in outputs/json/ and collects the word strings.
# This list will be injected into the Gemini prompt to prevent duplicates.
# Only runs when cache_hit is False (no file saved yet today).
def retrieve_node(state: SlangState):
    previous_words = get_previous_words()
    print(f"[RAG] Retrieved {len(previous_words)} previously used words.")
    return {"previous_words": previous_words}


# STEP 3 — Call Gemini with the retrieved history as context.
# previous_words from the state is passed into the prompt so Gemini
# knows which words to avoid. This is the core of the RAG pattern.
def generate_slangs_node(state: SlangState):
    slangs = generate_slangs(state["previous_words"])
    return {"generated_slangs": slangs}


# STEP 4 — Save the newly generated slangs to today's JSON file.
# Next time the app runs today, check_cache_node will find this file
# and skip the LLM call entirely.
def save_slangs_node(state: SlangState):
    save_daily_slangs(state["generated_slangs"])
    return state


# STEP 5 — Generate a PDF report and save to outputs/pdfs/YYYY-MM-DD.pdf
# Runs after save_slangs so the JSON and PDF are always created together.
# Skipped on cache-hit days (PDF was already created on first run today).
def pdf_node(state: SlangState):
    path = generate_pdf(state["generated_slangs"])
    print(f"[PDF] Report saved → {path}")
    return state


# STEP 6 — Print every slang as a styled panel in the terminal.
# Always runs last, whether data came from cache or from the LLM.
def display_slangs_node(state: SlangState):
    display_slangs(state["generated_slangs"])
    return state
