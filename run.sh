#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════╗"
echo "║   Voice Bot Analytics Dashboard      ║"
echo "╚══════════════════════════════════════╝"

# ── Backend ────────────────────────────────────────────────────────────────
cd "$ROOT/backend"

[ ! -d "venv" ] && python3 -m venv venv

venv/bin/pip install -r requirements.txt -q

echo "▶  Backend  →  http://localhost:8000"
venv/bin/uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# ── Frontend ───────────────────────────────────────────────────────────────
cd "$ROOT/frontend"

[ ! -d "node_modules" ] && npm install -q

echo "▶  Frontend →  http://localhost:3000"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "   API docs  →  http://localhost:8000/docs"
echo "   Press Ctrl+C to stop both"
echo ""

# ── Cleanup on Ctrl+C ──────────────────────────────────────────────────────
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

wait
