# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/schemas/slang_schema.py
# PURPOSE: Defines the data shape (schema) for a single slang word and a
#          collection of slangs. Every part of the app uses these models
#          to ensure the data is always consistent and correctly typed.
#
# WHAT IT DOES:
#   - SlangWord  → represents ONE slang entry with 5 fields
#   - SlangResponse → a wrapper that holds a LIST of SlangWord objects.
#                     Used by the LLM output parser to validate Gemini's response.
#
# WHY PYDANTIC:
#   Pydantic automatically validates types. If Gemini returns a number where
#   a string is expected, Pydantic raises an error immediately — preventing
#   silent bugs later in the pipeline.
#
# HOW IT CONNECTS:
#   → app/agent/slang_agent.py uses SlangResponse to parse Gemini's output
#   → app/utils/file_handler.py uses SlangWord to load/save slangs from JSON
#   → app/agent/state.py uses SlangWord in the LangGraph state definition
#   → app/rag/retriever.py uses SlangWord when loading the static dictionary
# ──────────────────────────────────────────────────────────────────────────────

from typing import List
from pydantic import BaseModel


class SlangWord(BaseModel):
    """Represents a single slang entry."""
    word: str       # The slang term e.g. "Rizz"
    meaning: str    # English explanation
    bengali: str    # Bengali translation
    tone: str       # How it is used e.g. "Casual", "Funny"
    example: str    # A sentence showing it in context


class SlangResponse(BaseModel):
    """
    Wrapper model used when parsing Gemini's structured output.
    Gemini is told to return JSON in this exact shape, and Pydantic
    validates that the response matches before we use the data.
    """
    slangs: List[SlangWord]
