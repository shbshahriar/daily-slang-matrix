# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/utils/file_handler.py
# PURPOSE: Handles all reading and writing of slang data to disk.
#          This is the caching layer of the app — it saves today's generated
#          slangs so the LLM doesn't need to be called again the same day.
#
# WHAT IT DOES:
#   - _today_file()        → builds the path for today's JSON file
#                            e.g. outputs/json/2026-05-19.json
#   - today_slangs_exist() → checks if that file already exists (True/False)
#   - load_daily_slangs()  → reads the file and returns a list of SlangWord objects
#   - save_daily_slangs()  → writes a list of SlangWord objects to the file
#
# WHY THIS MATTERS:
#   Every run of the app checks this file first. If it exists, we skip the
#   Gemini API call entirely — saving time, money, and API quota. A new file
#   is created each day automatically via the date-based filename.
#
# HOW IT CONNECTS:
#   → app/agent/nodes.py uses all 3 public functions:
#       - today_slangs_exist() in check_cache_node
#       - load_daily_slangs()  in check_cache_node (cache hit path)
#       - save_daily_slangs()  in save_slangs_node  (after LLM generation)
#   → app/schemas/slang_schema.py provides SlangWord for type conversion
# ──────────────────────────────────────────────────────────────────────────────

import json
from datetime import datetime
from pathlib import Path

from app.schemas.slang_schema import SlangWord


# All daily JSON files are saved inside this folder.
# Path() makes this work on both Windows and Linux without hardcoding slashes.
OUTPUT_DIR = Path("outputs/json")


def _today_file() -> Path:
    """
    Returns the full path for today's slang file.
    The filename is today's date so each day gets its own file automatically.
    Example: outputs/json/2026-05-19.json
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return OUTPUT_DIR / f"{today}.json"


def today_slangs_exist() -> bool:
    """
    Returns True if today's slang file already exists on disk.
    Used by check_cache_node to decide whether to call the LLM or not.
    """
    return _today_file().exists()


def load_daily_slangs() -> list[SlangWord]:
    """
    Reads today's JSON file and converts each entry into a SlangWord object.
    Called when cache_hit is True — the data is already on disk, no LLM needed.
    """
    with open(_today_file(), "r", encoding="utf-8") as f:
        data = json.load(f)
    # Convert each raw dict from JSON into a validated SlangWord object
    return [SlangWord(**item) for item in data]


def save_daily_slangs(slangs) -> Path:
    """
    Saves the generated list of SlangWord objects to today's JSON file.
    Called by save_slangs_node right after the LLM generates fresh slangs.
    ensure_ascii=False keeps Bengali characters readable in the file.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)   # create folder if it doesn't exist
    file_path = _today_file()
    with open(file_path, "w", encoding="utf-8") as f:
        # model_dump() converts each SlangWord object back to a plain dict for JSON
        json.dump([s.model_dump() for s in slangs], f, ensure_ascii=False, indent=4)
    return file_path
