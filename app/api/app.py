# ──────────────────────────────────────────────────────────────────────────────
# FILE: app/api/app.py
# PURPOSE: Creates the FastAPI application instance and mounts all routes.
#          This is the entry point for the HTTP server.
#
# HOW IT CONNECTS:
#   → app/api/routes.py  provides the APIRouter with all four endpoints
#   → Run locally with: uv run uvicorn app.api.app:app --reload
#   → In Docker: compose.yaml api service uses this as the uvicorn target
#     command: uvicorn app.api.app:app --host 0.0.0.0 --port 8000
# ──────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI

from app.api.routes import router


app = FastAPI(title="Daily Slang Matrix")

# Mount all routes — /, /today, /generate, /history
app.include_router(router)
