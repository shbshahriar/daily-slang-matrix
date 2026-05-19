# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/agent/slang_agent.py
# PURPOSE: Handles all communication with the Gemini LLM.
#          This is the only file that makes an API call.
#
# WHAT CHANGED FOR RAG:
#   The prompt now accepts {existing_words} — a comma-separated list of words
#   that Gemini has already generated before. Gemini is explicitly told to
#   avoid those words and return only NEW ones. This is the "Augmented" part
#   of Retrieval-Augmented Generation.
#
# CHAIN FLOW:
#   prompt (with existing_words injected)
#     → Gemini LLM
#     → with_structured_output validates the response as SlangResponse
#     → generate_slangs() returns List[SlangWord]
#
# HOW IT CONNECTS:
#   → Called by generate_slangs_node in app/agent/nodes.py
#   → Receives previous_words from the state (set by retrieve_node)
#   → Uses SlangResponse from app/schemas/slang_schema.py to validate output
# ──────────────────────────────────────────────────────────────────────────────

import os

from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from app.schemas.slang_schema import SlangResponse


load_dotenv()


# Prompt template is safe to build at module level — no API key needed here.
prompt = ChatPromptTemplate.from_template(
    "Generate 10 modern aesthetic English slang words.\n\n"
    "For each slang provide: word, meaning, bengali field in Banglish (romanized Bengali — e.g. 'Onek sundor' not 'অনেক সুন্দর'), tone, and an example sentence.\n\n"
    "DO NOT generate any of these words that were already used before:\n"
    "{existing_words}\n\n"
    "Return ONLY new, fresh words that are not in the list above."
)


def generate_slangs(previous_words: list[str]) -> list:
    """
    Calls Gemini with the list of already-used words as context.
    Gemini is instructed to avoid those words and generate fresh ones.

    Args:
        previous_words: list of slang words from past outputs (from retrieve_node)

    Returns:
        List[SlangWord] — 10 new, validated slang entries
    """
    # Build the LLM and chain here, not at module level.
    # On remote servers (Horizon), environment variables may not be available
    # at import time — reading the key at call time guarantees it's populated.
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.8,
    )
    chain = prompt | llm.with_structured_output(SlangResponse)

    context = ", ".join(previous_words[:100]) if previous_words else "None yet"
    response = chain.invoke({"existing_words": context})
    return response.slangs
