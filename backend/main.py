from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import demo_data as d
import database as db


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()


app = FastAPI(
    title="Voice Bot Analytics API",
    description="Demo API for the Voice Bot dashboard — Plivo + Gemini Live + MCP",
    version="1.0.0",
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

# ── Health check ──────────────────────────────────────────────────────────
@app.get("/health", tags=["meta"])
async def ping():
    return {"status": "ok", "version": "1.0.0"}

# ── Database ping ─────────────────────────────────────────────────────────
@app.get("/api/db-ping", tags=["meta"])
async def db_ping():
    """Verify PostgreSQL connectivity."""
    rows = await db.fetch("SELECT id, code, name, description, created_at FROM agent_types;")
    return {"status": "connected", "result": [dict(r) for r in rows]}

# ── Dashboard summary ─────────────────────────────────────────────────────
@app.get("/api/dashboard", tags=["dashboard"])
async def dashboard(range: str = RangeParam):
    """Top-level KPI summary from call_sessions, subscriptions, mcp_tool_calls."""
    return d.get_dashboard(range)

# ── Call volume chart ─────────────────────────────────────────────────────
@app.get("/api/call-volume", tags=["calls"])
async def call_volume(range: str = RangeParam):
    """Hourly / daily / weekly call volume from call_sessions.started_at."""
    return d.get_call_volume(range)

# ── Agent type performance ────────────────────────────────────────────────
@app.get("/api/agents", tags=["agents"])
async def agents(range: str = RangeParam):
    """All 4 agent type stats: outcomes, call counts, links, payments."""
    return d.get_agents(range)

# ── Call outcome breakdown ────────────────────────────────────────────────
@app.get("/api/outcomes", tags=["calls"])
async def outcomes(range: str = RangeParam):
    """call_outcomes grouped by outcome_type for the donut chart."""
    return d.get_outcomes(range)

# ── Subscription funnel ────────────────────────────────────────────────────
@app.get("/api/funnel", tags=["subscriptions"])
async def funnel(range: str = RangeParam):
    """Funnel: calls → interested → link sent → opened → paid."""
    return d.get_funnel(range)

# ── Follow-up queue ────────────────────────────────────────────────────────
@app.get("/api/follow-ups", tags=["follow-ups"])
async def follow_ups():
    """Pending follow_ups grouped by agent_type_id with reasons."""
    return d.get_follow_ups()

# ── Recent call sessions ──────────────────────────────────────────────────
@app.get("/api/sessions", tags=["calls"])
async def sessions(limit: int = Query(6, ge=1, le=20)):
    """Latest call_sessions joined with customers and agent_types."""
    return d.get_sessions(limit)

# ── MCP tool calls ────────────────────────────────────────────────────────
@app.get("/api/mcp-tools", tags=["mcp"])
async def mcp_tools(range: str = RangeParam):
    """mcp_tool_calls grouped by tool_name with counts and latency."""
    return d.get_mcp_tools(range)

# ── System health ─────────────────────────────────────────────────────────
@app.get("/api/health-status", tags=["system"])
async def health_status():
    """Service status: Plivo, Gemini Live, MCP, PostgreSQL, Quart."""
    return d.get_health()

# ── Subscription status split ─────────────────────────────────────────────
@app.get("/api/subscriptions/status", tags=["subscriptions"])
async def sub_status():
    """subscriptions grouped by status for the horizontal bar chart."""
    return d.get_sub_status()
