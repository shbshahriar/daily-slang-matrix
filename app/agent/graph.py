# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/agent/graph.py
# PURPOSE: Assembles all nodes into a runnable LangGraph pipeline.
#          Defines WHAT runs, in WHAT ORDER, and WHICH PATH to take.
#
# TWO POSSIBLE FLOWS:
#
#   Flow A — Cache HIT (slangs already saved today):
#   check_cache ──► display_slangs ──► END
#
#   Flow B — Cache MISS (first run of the day):
#   check_cache ──► retrieve ──► generate_slangs ──► save_slangs ──► generate_pdf ──► display_slangs ──► END
#
# WHY retrieve COMES AFTER check_cache:
#   There's no point scanning past outputs if today's slangs are already saved.
#   Retrieval only happens when we actually need to call the LLM.
#
# HOW IT CONNECTS:
#   → app/agent/nodes.py   provides all 5 node functions
#   → app/agent/state.py   provides SlangState (the shared data type)
#   → app/main.py          imports `graph` and calls graph.invoke({}) to run it
# ──────────────────────────────────────────────────────────────────────────────

from langgraph.graph import StateGraph, END

from app.agent.state import SlangState
from app.agent.nodes import (
    check_cache_node,
    retrieve_node,
    generate_slangs_node,
    save_slangs_node,
    pdf_node,
    display_slangs_node,
)

workflow = StateGraph(SlangState)

# Register all 5 nodes
workflow.add_node("check_cache",     check_cache_node)
workflow.add_node("retrieve",        retrieve_node)
workflow.add_node("generate_slangs", generate_slangs_node)
workflow.add_node("save_slangs",     save_slangs_node)
workflow.add_node("generate_pdf",    pdf_node)
workflow.add_node("display_slangs",  display_slangs_node)

# Always start here
workflow.set_entry_point("check_cache")


# After check_cache, branch based on whether today's file exists
def route_after_cache(state: SlangState):
    if state["cache_hit"]:
        return "display_slangs"   # file found → skip LLM, go straight to display
    return "retrieve"             # no file → retrieve history first, then generate

workflow.add_conditional_edges("check_cache", route_after_cache)

# RAG path: retrieve → generate → save → pdf → display
workflow.add_edge("retrieve",        "generate_slangs")
workflow.add_edge("generate_slangs", "save_slangs")
workflow.add_edge("save_slangs",     "generate_pdf")
workflow.add_edge("generate_pdf",    "display_slangs")
workflow.add_edge("display_slangs",  END)

graph = workflow.compile()
