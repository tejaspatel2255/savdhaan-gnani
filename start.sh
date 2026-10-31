#!/usr/bin/env bash
set -e
export PYTHONUNBUFFERED=1
PORT="${PORT:-10000}"
echo "Starting Savdhaan backend on 0.0.0.0:$PORT..."
exec uvicorn backend.main:app --host 0.0.0.0 --port "$PORT"
