# Daily Slang Matrix — Full Project Report

## Overview

Daily Slang Matrix is a fully automated system that generates 10 modern English slang words every day, enriched with meanings, Banglish (romanized Bengali) translations, tone labels, and example sentences. It uses a Retrieval-Augmented Generation pipeline backed by Google Gemini, persists output as JSON and PDF, exposes an HTTP API, and integrates with Claude Desktop via MCP — all running autonomously inside Docker on a daily cron schedule.

---

## Project Goal

Build a production-quality autonomous content generation system that:

- Generates fresh, non-repeating slang daily using an LLM
- Persists every output for history and deduplication
- Exports human-readable PDFs
- Runs on a schedule without manual intervention
- Is accessible via CLI, HTTP API, and AI assistant tools (MCP)
- Runs identically on any machine via Docker

---

## Final Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.13 |
| LLM | Google Gemini 2.5 Flash via `langchain-google-genai` |
| Orchestration | LangGraph (StateGraph with conditional edges) |
| LLM Abstraction | LangChain (prompt templates, chains) |
| Data Validation | Pydantic v2 |
| PDF Generation | fpdf2 |
| Terminal UI | Rich (panels, styled text) |
| HTTP API | FastAPI + Uvicorn |
| MCP Server | FastMCP |
| Environment | python-dotenv |
| Packaging | uv (replaces pip + requirements.txt) |
| Containerization | Docker + Docker Compose |
| Automation | cron (inside Docker container) |

---

## Architecture

### High-Level System

```
┌──────────────────────────────────────────────────────────────┐
│                       Interfaces                             │
│                                                              │
│   ┌───────────────┐  ┌───────────────┐  ┌────────────────┐  │
│   │  CLI / Cron   │  │  FastAPI      │  │  MCP Server    │  │
│   │  (scheduled)  │  │  (HTTP)       │  │  (Claude AI)   │  │
│   └──────┬────────┘  └──────┬────────┘  └───────┬────────┘  │
│          └─────────────────┬┘                   │            │
│                            │                    │            │
└────────────────────────────┼────────────────────┼────────────┘
                             │                    │
                    ┌────────▼────────────────────▼────────┐
                    │            Core Pipeline              │
                    │                                       │
                    │   ┌─────────────────────────────┐    │
                    │   │        LangGraph             │    │
                    │   │                              │    │
                    │   │  check_cache                 │    │
                    │   │      ↓ (cache miss)          │    │
                    │   │  retrieve (RAG)              │    │
                    │   │      ↓                       │    │
                    │   │  generate_slangs (Gemini)    │    │
                    │   │      ↓                       │    │
                    │   │  save_slangs (JSON)          │    │
                    │   │      ↓                       │    │
                    │   │  generate_pdf                │    │
                    │   │      ↓                       │    │
                    │   │  display_slangs (Rich)       │    │
                    │   └─────────────────────────────┘    │
                    │                                       │
                    └───────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              ↓              ↓              ↓
        outputs/json/  outputs/pdfs/    logs/
        YYYY-MM-DD.json YYYY-MM-DD.pdf  output.log
```

### LangGraph Conditional Flow

```
                    ┌─────────────┐
                    │ check_cache │
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
         cache HIT                 cache MISS
              │                         │
              ↓                         ↓
       display_slangs              retrieve
              │                    (RAG scan)
              ↓                         │
             END                        ↓
                                 generate_slangs
                                   (Gemini LLM)
                                        │
                                        ↓
                                   save_slangs
                                    (JSON write)
                                        │
                                        ↓
                                  generate_pdf
                                   (fpdf2)
                                        │
                                        ↓
                                 display_slangs
                                   (Rich UI)
                                        │
                                        ↓
                                       END
```

### RAG Flow

```
outputs/json/
├── 2026-05-01.json  ──┐
├── 2026-05-02.json  ──┤──→  extract all "word" fields
├── 2026-05-03.json  ──┤         │
└── ...              ──┘         ↓
                          deduplicate with set()
                                 │
                                 ↓
                    inject into Gemini prompt as
                    "DO NOT generate these words: ..."
                                 │
                                 ↓
                    Gemini generates 10 fresh words
```

### Docker Architecture

```
┌──────────────────────────────────────────┐
│           Docker Compose                 │
│                                          │
│  ┌─────────────────┐  ┌───────────────┐  │
│  │   scheduler     │  │     api       │  │
│  │                 │  │               │  │
│  │  entrypoint.sh  │  │  uvicorn      │  │
│  │       ↓         │  │  :8000        │  │
│  │  cron daemon    │  │               │  │
│  │       ↓ (8 AM)  │  └───────┬───────┘  │
│  │   cron.sh       │          │           │
│  │       ↓         │     port 8000        │
│  │  app/main.py    │          │           │
│  └────────┬────────┘          │           │
│           │                   │           │
│    ┌──────┴───────────────────┘           │
│    │         Shared Volumes               │
│    │  ./outputs → /app/outputs            │
│    │  ./logs    → /app/logs               │
│    └──────────────────────────────────────┘
└──────────────────────────────────────────┘
```

---

## Development Phases

### Phase 1 — Terminal UI with Rich

The first working version had no LLM. It loaded a static list of slang words and displayed them in the terminal. The goal was to establish the display layer first — what the output should look like — before building the generation logic behind it.

Rich was chosen over plain print() because the terminal output needed colour-coded fields, borders, and structured cards. Each slang word is rendered as a bordered panel with distinct colours per field: word in cyan, meaning in green, Banglish in yellow, tone in magenta, example in white.

### Phase 2 — Pydantic Schemas

A `SlangWord` model was introduced to enforce the structure of every slang entry. Every piece of data flowing through the system — from LLM output to JSON files to API responses — is validated against this schema. A second model, `SlangResponse`, wraps a list of `SlangWord` objects and was later critical for structured LLM output.

Pydantic v2 was used. The `.model_dump()` method serializes objects to plain dicts for JSON and API responses.

### Phase 3 — Gemini LLM Integration

Google Gemini 2.5 Flash was integrated via `langchain-google-genai`. A prompt template was written in LangChain using `ChatPromptTemplate` that instructs Gemini to generate 10 slang words in a specific format.

The API key is read from a `.env` file via `python-dotenv` and injected at runtime — never hardcoded.

### Phase 4 — LangChain Chain

The prompt template and LLM were composed into a LangChain chain using the pipe operator. This is the standard LangChain Expression Language (LCEL) pattern. The chain takes `existing_words` as input and returns a structured response.

Structured output via `with_structured_output(SlangResponse)` was used instead of a string output parser. This forces Gemini to return valid JSON that maps directly to the Pydantic model — eliminating the entire class of JSON parsing errors.

### Phase 5 — LangGraph Pipeline

The single function call was replaced with a LangGraph `StateGraph`. This added proper pipeline orchestration with:

- A shared `SlangState` TypedDict that flows through every node
- Six nodes: check_cache, retrieve, generate_slangs, save_slangs, generate_pdf, display_slangs
- Conditional branching: if today's JSON file already exists (cache hit), skip directly to display. If not, run the full generation pipeline.

LangGraph justified itself here by enabling the cache-bypass branch cleanly — a pattern that would have been messy with plain function calls.

### Phase 6 — RAG (Retrieval-Augmented Generation)

A `retriever.py` module was built to scan all previously saved JSON files in `outputs/json/`. It collects every word that has ever been generated, deduplicates using a set, and returns a flat list of strings.

This list is injected into the Gemini prompt as negative context: "do not generate any of these words." This prevents the system from producing duplicate words across days — the core value of the RAG layer.

A static `slang_dictionary.json` with 100 hand-curated entries was also added as a reference dataset.

### Phase 7 — PDF Generation

fpdf2 was chosen after evaluating three PDF libraries. Each entry gets a numbered block with word, meaning, Banglish, tone, and example in an italic sentence.

The design uses Helvetica throughout (no custom fonts) — a deliberate choice tied to the Banglish decision described in the problems section below.

### Phase 8 — Automation (cron in Docker)

`cron.sh` runs the CLI pipeline, appends timestamped output to `logs/output.log`, and is triggered by a crontab entry set to 8 AM daily. An `entrypoint.sh` script captures the container's injected environment variables (from `--env-file`) and writes them to `/etc/environment` before starting cron — this is necessary because cron runs with a bare environment and would not otherwise see `GOOGLE_API_KEY`.

### Phase 9 — Docker

A multi-stage-style setup using the official `ghcr.io/astral-sh/uv` base image. Dependencies are installed before application code is copied — a standard layer caching pattern that makes rebuilds significantly faster when only application code changes.

`compose.yaml` defines two services from the same image: `scheduler` (cron daemon) and `api` (uvicorn). Both share the `outputs/` volume so generated files are accessible from both services and persist outside the container.

`.env` is never baked into the image — it is always injected at runtime via `--env-file`.

### Phase 10 — MCP Integration

A FastMCP server exposes three tools to Claude Desktop and any MCP-compatible AI assistant: `get_daily_slangs`, `generate_daily_pdf`, and `get_previous_slangs`.

The MCP server intentionally bypasses the LangGraph graph and calls the underlying functions directly. This was a deliberate design decision: the graph's final node (`display_slangs`) writes Rich-formatted text to stdout. MCP uses stdio as its transport protocol, so any non-JSON output on stdout would corrupt the MCP communication stream.

### Phase 11 — FastAPI

Four HTTP routes were wired up: a health check, a cached today endpoint, a live generation endpoint, and a history listing. The generation endpoint follows the same pattern as the MCP server — calls the agent functions directly, not through the graph.

---

## Problems Faced and Solutions

### Problem 1 — UnicodeEncodeError on Windows (Fire Emoji)

**What happened:** The terminal header contained a fire emoji. On Windows, the default terminal encoding is cp1252, which cannot represent Unicode characters outside the Latin-1 range. The application crashed immediately on startup with a `UnicodeEncodeError`.

**What was tried:** Adding `sys.stdout.reconfigure(encoding="utf-8")` to fix the encoding.

**Final solution:** Reconfigure stdout to UTF-8 before any output, and remove the emoji from the header string entirely. The reconfigure call must happen before any Rich or print import is used.

---

### Problem 2 — Bengali Text Broken in Terminal

**What happened:** Bengali script characters (e.g. অনেক সুন্দর) rendered as boxes or question marks in the Windows terminal. Even after fixing the encoding issue, the terminal font (Consolas, Cascadia Code) does not include Bengali Unicode glyphs.

**What was tried:** Multiple font configurations, UTF-8 encoding fixes.

**Final solution:** Switch from Bengali script to Banglish — romanized Bengali written in English characters (e.g. "Onek sundor"). This works universally in any terminal, any font, any platform. The field was renamed from `bengali` to reflect Banglish, and the prompt instructs Gemini explicitly to output romanized Bengali only. This decision cascaded to the PDF and all display layers.

---

### Problem 3 — Rich Table Layout Broken with Bengali

**What happened:** Before switching to Banglish, Rich was used with a Table layout. Rich calculates column widths by character count, but Bengali characters are double-width Unicode — Rich miscounted widths and the table columns misaligned badly.

**Final solution:** Replaced the Table with a Panel-per-card layout. Each slang word gets its own bordered panel. There are no column width calculations to go wrong.

---

### Problem 4 — Wrong Environment Variable Name

**What happened:** The slang agent code read `GEMINI_API_KEY` from the environment, but the `.env` file defined `GOOGLE_API_KEY`. Every call to Gemini failed with a validation error about a missing API key.

**Final solution:** Align the variable name in code with what `langchain-google-genai` expects: `GOOGLE_API_KEY`.

---

### Problem 5 — Gemini Returning Malformed JSON

**What happened:** Gemini was asked to return JSON via a plain string prompt. It occasionally returned valid-looking JSON with a stray character (a literal `T` appended outside the JSON block). LangChain's `PydanticOutputParser` could not parse this and raised an `OutputParserException`.

**Root cause:** Asking an LLM to format its own output as JSON and parse that string is inherently fragile. The model hallucinates or adds commentary.

**Final solution:** Switch to `llm.with_structured_output(SlangResponse)`. This uses Gemini's native function-calling / structured output mode, which enforces the schema at the API level. The response maps directly to the Pydantic model without any string parsing step.

---

### Problem 6 — PDF Library Failures (Three Libraries)

This was the most complex problem in the project and went through three libraries before a solution was found.

**Attempt 1 — ReportLab**

ReportLab is a widely-used Python PDF library. Bengali script requires a shaping engine (a system that combines individual characters into correct ligatures). ReportLab has no Indic script shaping. Even with the Vrinda Bengali font registered, the text rendered as disconnected individual glyphs — visually broken and unreadable.

**Attempt 2 — WeasyPrint**

WeasyPrint renders HTML/CSS to PDF and uses system-level text shaping via HarfBuzz and Pango. In theory this should handle Bengali. In practice, WeasyPrint on Windows requires GTK3 system libraries (`libgobject-2.0`). These are not installable via pip — they require a full GTK runtime. This failed with an `OSError` and was abandoned.

**Attempt 3 — fpdf2 with uharfbuzz**

fpdf2 has a `uharfbuzz` integration for text shaping. This was installed and configured. Some Bengali characters rendered correctly but others were still broken — the shaping was inconsistent.

**Final solution:** Switch to Banglish in the PDF as well. With Banglish, plain Helvetica renders everything correctly with zero font dependencies. The `uharfbuzz`, `reportlab`, and `weasyprint` packages were all removed from `pyproject.toml`. 11 packages were uninstalled.

---

### Problem 7 — fpdf2 Cursor Bug with multi_cell

**What happened:** All PDF content was being compressed into the right edge of the page, or raising "Not enough horizontal space" errors.

**Two separate root causes were found:**

1. `set_margins()` was being called after `add_page()`. In fpdf2, margins must be set before the first page is added — calling it after has no effect and the page uses default margins.

2. `multi_cell()` in fpdf2 moves the cursor to the right edge of the cell after rendering, not to the left margin. Every subsequent `multi_cell` call started from the right edge and immediately ran out of space.

**Final solution:** Move `set_margins()` before `add_page()`, and add `new_x="LMARGIN", new_y="NEXT"` to every single `multi_cell` call. These parameters reset the cursor to the left margin after each cell.

---

### Problem 8 — Cron Cannot See Environment Variables

**What happened:** Docker injects environment variables via `--env-file` into the container's main process. Cron is a separate daemon — it spawns jobs with its own minimal environment and does not inherit the variables that Docker injected. `GOOGLE_API_KEY` was invisible to the cron job, causing the Gemini call to fail silently.

**Final solution:** `entrypoint.sh` runs before cron starts. It calls `printenv` and appends the entire current environment to `/etc/environment`. Cron reads `/etc/environment` when starting jobs, so all injected variables become available to every cron-triggered script.

---

### Problem 9 — MCP Server Would Corrupt Its Own Protocol

**What happened:** The LangGraph pipeline ends with a `display_slangs` node that writes Rich-formatted text to stdout. MCP uses stdin/stdout as its transport — every byte on stdout is part of the JSON-RPC communication stream. Running the graph from inside the MCP server would have written Rich panel output directly into the MCP protocol, corrupting every response.

**Final solution:** The MCP server bypasses the graph entirely and calls the underlying functions (`slang_agent.generate_slangs`, `file_handler.save_daily_slangs`, `pdf_generator.generate_pdf`) directly. The display node is never invoked in the MCP context.

---

## Key Design Decisions

**uv over pip**
uv manages dependencies, virtual environments, and lockfiles significantly faster than pip. `pyproject.toml` and `uv.lock` replace `requirements.txt`. The Docker image uses the official uv base image.

**LangGraph over plain functions**
The cache-bypass conditional branch — skip the entire generation pipeline if today's file already exists — is cleanly expressed as a conditional edge in LangGraph. Without it, the same logic would require manual if/else branching spread across multiple call sites.

**with_structured_output over output parsers**
Structured output uses Gemini's native schema enforcement at the API level. Output parsers parse strings, which is fragile. The switch eliminated an entire class of runtime errors.

**Banglish over Bengali script**
Bengali script requires a full Unicode shaping pipeline (HarfBuzz + Pango or equivalent) at every layer: terminal, PDF, and any downstream system. Banglish is ASCII-compatible and works everywhere without special fonts or shaping engines. Given the scope of the project, Banglish was the correct tradeoff.

**Same Docker image, two services**
The `scheduler` and `api` services in `compose.yaml` both build from the same Dockerfile. The image contains everything needed for both. The `api` service overrides the default CMD to run uvicorn instead of the cron entrypoint. This avoids maintaining two separate Dockerfiles.

**MCP calls functions directly, not the graph**
Covered in Problem 9 above. The graph is for the CLI pipeline. The MCP and API layers call the underlying functions directly to avoid side effects (terminal output, logging) that are inappropriate in those contexts.

---

## Package Cleanup History

During development, three packages were installed and later removed after better solutions were found:

| Package | Reason installed | Reason removed |
|---|---|---|
| reportlab | Bengali PDF generation | No Indic script shaping |
| weasyprint | Bengali PDF via HTML/CSS | Requires GTK system libraries on Windows |
| uharfbuzz | Text shaping for fpdf2 | Inconsistent Bengali rendering — switched to Banglish |

---

## Final Project Structure

```
daily-slang-matrix/
│
├── app/
│   ├── agent/
│   │   ├── graph.py          LangGraph pipeline assembly
│   │   ├── nodes.py          All six pipeline node functions
│   │   ├── slang_agent.py    Gemini LLM chain
│   │   └── state.py          Shared LangGraph state schema
│   │
│   ├── api/
│   │   ├── app.py            FastAPI application instance
│   │   └── routes.py         HTTP route handlers
│   │
│   ├── mcp_server.py         FastMCP server with three tools
│   ├── main.py               CLI entry point
│   │
│   ├── rag/
│   │   ├── retriever.py      RAG: scans past outputs for context
│   │   └── slang_dictionary.json   100 curated reference slangs
│   │
│   ├── schemas/
│   │   └── slang_schema.py   Pydantic models (SlangWord, SlangResponse)
│   │
│   ├── ui/
│   │   ├── pdf_generator.py  fpdf2 PDF export
│   │   └── terminal_ui.py    Rich terminal display
│   │
│   └── utils/
│       └── file_handler.py   JSON cache read/write
│
├── outputs/
│   ├── json/                 YYYY-MM-DD.json per day
│   └── pdfs/                 YYYY-MM-DD.pdf per day
│
├── logs/
│   └── output.log            Cron execution history
│
├── Dockerfile                uv base image, cron setup
├── compose.yaml              scheduler + api services
├── entrypoint.sh             Env bridge for cron
├── cron.sh                   Daily runner script
├── crontab                   0 8 * * * schedule
├── pyproject.toml            Dependencies (uv)
├── uv.lock                   Lockfile
├── .env                      GOOGLE_API_KEY (never committed)
├── .gitignore
└── .dockerignore
```

---

## API Reference

| Method | Route | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/today` | Today's slangs from cache (404 if not generated yet) |
| GET | `/generate` | Generate today's slangs via Gemini and save |
| GET | `/history` | List all past JSON output files |

Interactive docs available at `http://localhost:8000/docs` when the API service is running.

---

## MCP Tools

| Tool | Description |
|---|---|
| `get_daily_slangs` | Returns today's 10 slangs. Generates if not yet created. |
| `generate_daily_pdf` | Generates today's PDF and returns file path. |
| `get_previous_slangs` | Returns all words generated on past days. |

---

## Running the Project

### Local (CLI)

```
uv run python -m app.main
```

### Docker (full system)

```
docker compose up --build -d
```

Starts both the scheduler (cron at 8 AM daily) and the API (port 8000).

### MCP (Claude Desktop)

Point Claude Desktop's MCP config at `app.mcp_server` with the project directory as working directory and `GOOGLE_API_KEY` in the environment.

---

## What This Project Demonstrates

- Multi-layer Python application architecture (CLI, API, MCP, scheduled job — all from one codebase)
- LangGraph for stateful conditional pipelines
- RAG without a vector database — file-system retrieval is sufficient when the corpus is small and exact-match deduplication is the goal
- Structured LLM output via native schema enforcement
- Docker multi-service setup from a single image
- Environment variable safety in containers (never baked in, always injected)
- Cross-platform text rendering constraints and practical workarounds
