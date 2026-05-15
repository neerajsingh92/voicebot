from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import database as db
import db_queries as q

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(
    title="Voice Bot Analytics API",
    description="FastAPI backend — Plivo + Gemini Live + MCP + PostgreSQL",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RangeParam = Query("1d", description="Time range: 1d | 7d | 30d")

# ── Health ────────────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def ping():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/db-ping", tags=["meta"])
async def db_ping():
    rows = await db.fetch("SELECT id, code, name FROM agent_types ORDER BY id")
    return {"status": "connected", "agent_types": [dict(r) for r in rows]}

# ── Dashboard ─────────────────────────────────────────────────────────────
@app.get("/api/dashboard", tags=["dashboard"])
async def dashboard(range: str = RangeParam):
    return await q.get_dashboard(range)

# ── Call volume chart ─────────────────────────────────────────────────────
@app.get("/api/call-volume", tags=["calls"])
async def call_volume(range: str = RangeParam):
    return await q.get_call_volume(range)

# ── Agent cards ───────────────────────────────────────────────────────────
@app.get("/api/agents", tags=["agents"])
async def agents(range: str = RangeParam):
    return await q.get_agents(range)

# ── Outcome donut ─────────────────────────────────────────────────────────
@app.get("/api/outcomes", tags=["calls"])
async def outcomes(range: str = RangeParam):
    return await q.get_outcomes(range)

# ── Subscription funnel ────────────────────────────────────────────────────
@app.get("/api/funnel", tags=["subscriptions"])
async def funnel(range: str = RangeParam):
    return await q.get_funnel(range)

# ── Follow-up queue ────────────────────────────────────────────────────────
@app.get("/api/follow-ups", tags=["follow-ups"])
async def follow_ups(range: str = RangeParam):
    return await q.get_follow_ups(range)

# ── Recent sessions ────────────────────────────────────────────────────────
@app.get("/api/sessions", tags=["calls"])
async def sessions(range: str = RangeParam, limit: int = Query(6, ge=1, le=20)):
    return await q.get_sessions(range, limit)

# ── MCP tools ─────────────────────────────────────────────────────────────
@app.get("/api/mcp-tools", tags=["mcp"])
async def mcp_tools(range: str = RangeParam):
    return await q.get_mcp_tools(range)

# ── System health ─────────────────────────────────────────────────────────
@app.get("/api/health-status", tags=["system"])
async def health_status():
    return await q.get_health()

# ── Subscription status ────────────────────────────────────────────────────
@app.get("/api/subscriptions/status", tags=["subscriptions"])
async def sub_status(range: str = RangeParam):
    return await q.get_sub_status(range)

# ══════════════════════════════════════════════════════════════════════════
#  CONVERSATIONS / TEAMS  section
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/conversations", tags=["conversations"])
async def conversations(
    range:  str = RangeParam,
    limit:  int = Query(20, ge=1, le=100),
    offset: int = Query(0,  ge=0),
):
    """
    Paginated list of call sessions with transcript preview.
    Use ?range=1d|7d|30d, ?limit=, ?offset= for pagination.
    """
    return await q.get_conversations(range, limit, offset)


@app.get("/api/conversations/{session_id}", tags=["conversations"])
async def conversation_detail(session_id: str):
    """
    Full detail for one call session:
    transcript, MCP tool calls, outcome, follow-up, subscription link.
    """
    result = await q.get_conversation_detail(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found")
    return result


@app.get("/api/teams", tags=["conversations"])
async def team_stats(range: str = RangeParam):
    """
    Per-agent-type breakdown: call counts, completion rate,
    avg duration, outcome distribution, MCP usage.
    """
    return await q.get_team_stats(range)


# ── Serve built React frontend (production) ───────────────────────────────
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        return FileResponse(STATIC_DIR / "index.html")
