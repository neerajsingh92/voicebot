#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════╗"
echo "║   Voice Bot Analytics Dashboard      ║"
echo "╚══════════════════════════════════════╝"

# ── Use nvm Node if available (system node may be too old for Vite) ────────
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

NODE_BIN="$(command -v node)"
NODE_VER="$($NODE_BIN --version 2>/dev/null)"
echo "   Node: $NODE_VER  ($NODE_BIN)"

# ── Backend ────────────────────────────────────────────────────────────────
cd "$ROOT/backend"

[ ! -d "venv" ] && python3 -m venv venv

venv/bin/pip install -r requirements.txt -q

echo "▶  Backend  →  http://localhost:8000"
venv/bin/uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# ── Frontend ───────────────────────────────────────────────────────────────
cd "$ROOT/frontend"

[ ! -d "node_modules" ] && npm install

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
