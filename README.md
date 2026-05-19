# Daily Slang Matrix

[![GitHub](https://img.shields.io/badge/GitHub-shbshahriar%2Fdaily--slang--matrix-181717?logo=github)](https://github.com/shbshahriar/daily-slang-matrix)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-shbshahriar%2Fdaily--slang--matrix-2496ED?logo=docker&logoColor=white)](https://hub.docker.com/r/shbshahriar/daily-slang-matrix)
[![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)

An autonomous daily slang generator powered by Google Gemini, LangGraph, and RAG. Every morning it generates 10 fresh modern English slang words with meanings, Banglish translations, tone labels, and example sentences — saves them as JSON and PDF, and exposes them through a CLI, REST API, and MCP tools for Claude Desktop.

---

## What It Does

- Generates 10 new English slang words daily using Google Gemini
- Translates each word into **Banglish** (romanized Bengali) for accessibility
- Retrieves all previously generated words and injects them into the prompt so the same word is **never repeated across days**
- Saves output as **JSON** (for history) and **PDF** (for reading)
- Runs automatically every day at 8 AM via **cron inside Docker**
- Serves data over **HTTP** via FastAPI
- Exposes tools to **Claude Desktop** via MCP

---

## Demo

```
╭─────────────────────────────────╮
│     Daily Aesthetic Slang Drop  │
╰─────────────────────────────────╯

╭─────────────────────────────────╮
│ Rizz                            │
│ Meaning : Natural charm         │
│ Banglish: Swabhavik akorshon    │
│ Tone    : Casual                │
│ Example : He walked in with     │
│           unmatched rizz.       │
╰─────────────────────────────────╯
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                         Interfaces                           │
│                                                              │
│   ┌───────────────┐   ┌────────────────┐   ┌────────────┐   │
│   │  CLI / Cron   │   │  FastAPI :8000 │   │    MCP     │   │
│   │  (scheduled)  │   │  (HTTP)        │   │  (Claude)  │   │
│   └──────┬────────┘   └──────┬─────────┘   └─────┬──────┘   │
│          └────────────────── ┼ ─────────────────┘            │
└──────────────────────────────┼───────────────────────────────┘
                               │
                  ┌────────────▼────────────┐
                  │       LangGraph         │
                  │                         │
                  │  check_cache            │
                  │    ├─ HIT  → display    │
                  │    └─ MISS ↓            │
                  │  retrieve  (RAG)        │
                  │    ↓                    │
                  │  generate  (Gemini)     │
                  │    ↓                    │
                  │  save      (JSON)       │
                  │    ↓                    │
                  │  pdf       (fpdf2)      │
                  │    ↓                    │
                  │  display   (Rich)       │
                  └────────────┬────────────┘
                               │
              ┌────────────────┼─────────────┐
              ↓                ↓             ↓
        outputs/json/    outputs/pdfs/    logs/
```

### RAG Flow

Previously generated words are retrieved from `outputs/json/*.json` and injected into the Gemini prompt as negative context — "do not generate these words." This prevents any word from appearing twice across days without needing a vector database.

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Google Gemini 2.5 Flash |
| Orchestration | LangGraph |
| LLM Abstraction | LangChain |
| Data Validation | Pydantic v2 |
| PDF Export | fpdf2 |
| Terminal UI | Rich |
| HTTP API | FastAPI + Uvicorn |
| MCP Server | FastMCP |
| Packaging | uv |
| Containerization | Docker + Compose |
| Automation | cron (inside Docker) |

---

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) installed
- Google Gemini API key — get one free at [aistudio.google.com](https://aistudio.google.com)

### 1. Clone and install

```bash
git clone https://github.com/shbshahriar/daily-slang-matrix.git
cd daily-slang-matrix
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your key:
# GOOGLE_API_KEY=your-key-here
```

### 3. Run

```bash
uv run python -m app.main
```

---

## Docker

### Pull from Docker Hub

```bash
docker pull shbshahriar/daily-slang-matrix
```

### Run with Docker Compose

The full system runs in two containers — a cron scheduler and an HTTP API — both built from the same image.

```bash
# Start both services
docker compose up -d

# Or build from source
docker compose up --build -d

# Watch scheduler logs
docker compose logs -f scheduler

# Watch API logs
docker compose logs -f api
```

The cron job runs at **8 AM daily**. To change the schedule, edit `crontab`:

```
0 8 * * * root /app/cron.sh
```

Generated files are written to `./outputs/` and logs to `./logs/` on your host machine via volume mounts.

---

## API Reference

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/today` | Today's slangs from cache. Returns 404 if not generated yet. |
| GET | `/generate` | Generate today's slangs via Gemini and save them. |
| GET | `/history` | List all past output files by date. |

Interactive docs: `http://localhost:8000/docs`

---

## MCP — Claude Desktop Integration

Add to `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "daily-slang": {
      "command": "uv",
      "args": ["run", "python", "-m", "app.mcp_server"],
      "cwd": "C:\\path\\to\\daily-slang-matrix",
      "env": {
        "GOOGLE_API_KEY": "your-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. Three tools will be available:

| Tool | Description |
|---|---|
| `get_daily_slangs` | Returns today's 10 slangs. Generates if not yet created. |
| `generate_daily_pdf` | Creates the PDF and returns the file path. |
| `get_previous_slangs` | Returns all words generated on previous days. |

---

## Project Structure

```
daily-slang-matrix/
│
├── app/
│   ├── agent/
│   │   ├── graph.py           LangGraph pipeline (nodes + edges + branching)
│   │   ├── nodes.py           All six pipeline step functions
│   │   ├── slang_agent.py     Gemini LLM chain with structured output
│   │   └── state.py           Shared TypedDict state for LangGraph
│   │
│   ├── api/
│   │   ├── app.py             FastAPI application instance
│   │   └── routes.py          HTTP route handlers
│   │
│   ├── mcp_server.py          FastMCP server — three tools for Claude Desktop
│   ├── main.py                CLI entry point
│   │
│   ├── rag/
│   │   ├── retriever.py       Scans past outputs to build deduplication context
│   │   └── slang_dictionary.json   100 curated reference slangs
│   │
│   ├── schemas/
│   │   └── slang_schema.py    Pydantic models: SlangWord, SlangResponse
│   │
│   ├── ui/
│   │   ├── pdf_generator.py   fpdf2 PDF export
│   │   └── terminal_ui.py     Rich terminal panel display
│   │
│   └── utils/
│       └── file_handler.py    JSON cache read/write
│
├── outputs/
│   ├── json/                  YYYY-MM-DD.json — one file per day
│   └── pdfs/                  YYYY-MM-DD.pdf  — one file per day
│
├── logs/
│   └── output.log             Timestamped cron execution history
│
├── Dockerfile                 uv base image, cron installed
├── compose.yaml               scheduler + api services
├── entrypoint.sh              Bridges Docker env vars into cron's environment
├── cron.sh                    Daily runner with logging
├── crontab                    Schedule: 0 8 * * *
├── pyproject.toml             Dependencies managed by uv
└── .env.example               Environment variable template
```

---

## How the Cache Works

On every run, the pipeline first checks whether `outputs/json/YYYY-MM-DD.json` exists for today.

- **Cache hit** — load from disk, skip the Gemini API call entirely, go straight to display
- **Cache miss** — scan all past files for previously used words, call Gemini with that context, save the result, generate PDF, display

This means the LLM is called **at most once per day**, regardless of how many times the app runs.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |

---

## License

MIT
