# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/agent/state.py
# PURPOSE: Defines the shared memory (state) that LangGraph passes between
#          every node in the pipeline.
#
# FIELDS:
#   - previous_words   → list of slang words already generated on past days.
#                         Set by retrieve_node. Passed to Gemini so it avoids
#                         repeating words it already generated before.
#   - generated_slangs → the list of SlangWord objects flowing through the
#                         pipeline from generation/cache all the way to display.
#   - cache_hit        → True  = today's file already exists, skip LLM call.
#                         False = no file today, run the full RAG + generate flow.
#
# HOW IT CONNECTS:
#   → app/agent/graph.py     passes SlangState as the state type to StateGraph
#   → app/agent/nodes.py     every node reads/writes this state
#   → app/schemas/slang_schema.py provides the SlangWord type used here
# ──────────────────────────────────────────────────────────────────────────────

from typing import TypedDict, List

from app.schemas.slang_schema import SlangWord


class SlangState(TypedDict):
    previous_words: List[str]           # words from past outputs — used to avoid duplicates
    generated_slangs: List[SlangWord]   # slangs carried through the pipeline
    cache_hit: bool                     # did we find today's file on disk?
