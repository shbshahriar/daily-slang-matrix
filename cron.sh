#!/bin/bash

mkdir -p /app/logs

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting daily slang generation" >> /app/logs/output.log

cd /app
uv run python -m app.main >> /app/logs/output.log 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Done" >> /app/logs/output.log
