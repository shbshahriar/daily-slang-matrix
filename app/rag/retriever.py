# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/rag/retriever.py
# PURPOSE: The retrieval layer of the RAG system.
#          It scans all previously saved output files and collects every slang
#          word that has already been generated. This list is then passed to
#          Gemini as context so it never generates duplicate words.
#
# FUNCTIONS:
#   - get_previous_words() → scans outputs/json/*.json and returns a deduplicated
#                             list of all words already generated on past days.
#                             This is the core of RAG — retrieval from history.
#
#   - load_slangs()        → reads the static slang_dictionary.json (100 curated
#                             words). Available as a reference/fallback dataset.
#
#   - get_daily_slangs()   → returns a limited slice from the static dictionary.
#
# HOW IT CONNECTS:
#   → app/agent/nodes.py calls get_previous_words() inside retrieve_node()
#   → The returned word list goes into SlangState["previous_words"]
#   → app/agent/slang_agent.py receives previous_words and injects them
#     into the Gemini prompt as context to avoid repetition
# ──────────────────────────────────────────────────────────────────────────────

import json
from pathlib import Path

from app.schemas.slang_schema import SlangWord


# Where all daily generated JSON files are stored
OUTPUT_DIR = Path("outputs/json")


def get_previous_words() -> list[str]:
    """
    Scans every saved output file in outputs/json/ and collects all slang words
    that have already been generated on previous days.

    Returns a deduplicated list of word strings.
    Example: ["Rizz", "Delulu", "Slay", "Vibe check", ...]

    This is passed to Gemini as context so it knows what NOT to generate again.
    If no output files exist yet (first ever run), returns an empty list.
    """
    if not OUTPUT_DIR.exists():
        return []

    words = []

    for file in OUTPUT_DIR.glob("*.json"):
        with open(file, encoding="utf-8") as f:
            data = json.load(f)
        for item in data:
            words.append(item["word"])

    # Use set() to remove duplicates, then convert back to list
    return list(set(words))


def load_slangs() -> list[SlangWord]:
    """
    Loads the static hand-curated slang dictionary (100 entries).
    This is a fixed reference dataset — it doesn't change unless you edit the JSON.
    """
    with open("app/rag/slang_dictionary.json", "r", encoding="utf-8") as file:
        data = json.load(file)
    return [SlangWord(**item) for item in data]


def get_daily_slangs(limit: int = 10) -> list[SlangWord]:
    """
    Returns the first `limit` entries from the static dictionary.
    Useful for testing the display pipeline without making an LLM call.
    """
    return load_slangs()[:limit]
