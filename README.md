# Voice Bot Analytics Dashboard

React + FastAPI analytics dashboard for the Plivo · Gemini Live · MCP voice bot system.
Built from the PostgreSQL schema: customers, call_sessions, call_outcomes, subscriptions,
subscription_links, follow_ups, conversation_transcripts, mcp_tool_calls.

---

## Prerequisites

| Tool       | Version  | Install                          |
|------------|----------|----------------------------------|
| Python     | 3.10+    | https://python.org               |
| Node.js    | 18+      | https://nodejs.org               |
| npm        | 9+       | bundled with Node.js             |

---

## Quick Start (Two terminals)

### Terminal 1 — Backend

```bash
cd voicebot-dashboard/backend

# Create virtual environment
python -m venv venv

# Activate
# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload --port 8000
```

Backend will be live at → http://localhost:8000
Swagger docs at         → http://localhost:8000/docs

---

### Terminal 2 — Frontend

```bash
cd voicebot-dashboard/frontend

# Install npm dependencies
npm install

# Start the dev server
npm run dev
```

Frontend will be live at → http://localhost:3000

---

## API Endpoints

All endpoints are prefixed with `/api`. Swagger UI: http://localhost:8000/docs

| Method | Endpoint                    | Description                            |
|--------|-----------------------------|----------------------------------------|
| GET    | /api/dashboard              | KPI summary (range: 1d/7d/30d)        |
| GET    | /api/call-volume            | Hourly/daily/weekly call volume        |
| GET    | /api/agents                 | 4 agent type stats + outcomes          |
| GET    | /api/outcomes               | call_outcomes grouped by type          |
| GET    | /api/funnel                 | Subscription conversion funnel         |
| GET    | /api/follow-ups             | Pending follow_ups by agent type       |
| GET    | /api/sessions               | Recent call_sessions with customers    |
| GET    | /api/mcp-tools              | mcp_tool_calls grouped by tool_name    |
| GET    | /api/health-status          | Plivo / Gemini / MCP / DB status       |
| GET    | /api/subscriptions/status   | Subscription status split              |

Query parameter: `?range=1d` (default), `?range=7d`, `?range=30d`

---

## Project Structure

```
voicebot-dashboard/
├── backend/
│   ├── main.py            FastAPI app + all routes
│   ├── demo_data.py       In-memory demo datasets for all endpoints
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js     Dev proxy: /api → localhost:8000
│   ├── package.json
│   └── src/
│       ├── main.jsx       React entry point
│       ├── App.jsx        Root component — fetches all data
│       ├── index.css      Theme tokens (dark/light CSS variables)
│       ├── api.js         Fetch client — all API calls in one place
│       ├── hooks/
│       │   └── useApi.js  useApi() + useTheme() hooks
│       └── components/
│           ├── Header.jsx       Theme toggle + range selector
│           ├── KpiGrid.jsx      8 KPI summary cards
│           ├── VolumeChart.jsx  Chart.js bar chart (call volume)
│           ├── AgentCards.jsx   4 agent performance cards
│           ├── MiddleRow.jsx    Funnel + Donut + Follow-up queue
│           └── BottomRow.jsx    Sessions table + MCP + Health
```

---

## Theme System

Three modes selectable from the header toggle:

| Mode  | Behaviour                                  |
|-------|--------------------------------------------|
| Dark  | Forces dark theme (default)                |
| Light | Forces light theme                         |
| Auto  | Follows OS `prefers-color-scheme`          |

Preference is persisted in `localStorage` under key `vb-theme`.

---

## Production Build

```bash
# Build the frontend
cd frontend
npm run build          # outputs to frontend/dist/

# Serve static files from FastAPI (optional)
# Copy dist/ into backend/static/ and mount with StaticFiles
```

---

## Connecting to a Real Database

Replace the functions in `backend/demo_data.py` with real
SQLAlchemy queries against your PostgreSQL database.
The DB schema SQL is in `schema.sql` (from the earlier step).

```python
# Example: replace get_dashboard() with a real query
async def get_dashboard(range_: str):
    async with AsyncSessionLocal() as db:
        total = await db.scalar(select(func.count()).select_from(CallSession))
        ...
```

---

## Troubleshooting

**CORS error in browser** — make sure the backend is running on port 8000.
The Vite proxy (`vite.config.js`) forwards `/api` requests automatically in dev.

**`npm install` fails** — ensure Node.js ≥ 18: `node --version`

**`uvicorn` not found** — activate your virtual environment first.

**Port conflict** — change ports:
- Backend: `uvicorn main:app --port 8001`
- Frontend: `npm run dev -- --port 3001`
- Update `vite.config.js` proxy target to match.
