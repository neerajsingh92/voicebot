"""
All real SQL queries against the newspaper_agent DB.
Every function accepts an optional `range_` param ("1d" | "7d" | "30d")
which filters by started_at / created_at using a parameterised date boundary
— no string interpolation, safe against SQL injection.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import database as db

# ── helpers ────────────────────────────────────────────────────────────────

RANGE_DAYS = {"1d": 1, "7d": 7, "30d": 30}

def _since(range_: str) -> datetime:
    days = RANGE_DAYS.get(range_, 1)
    return datetime.now(timezone.utc) - timedelta(days=days)


def _fmt_duration(seconds: int | None) -> str:
    if not seconds:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{m}m {s:02d}s"


# ── KPI dashboard ──────────────────────────────────────────────────────────

async def get_dashboard(range_: str = "1d") -> dict:
    since = _since(range_)

    row = await db.fetchrow("""
        SELECT
            COUNT(*)                                            AS total_calls,
            COUNT(*) FILTER (WHERE call_status = 'completed')  AS completed_calls,
            ROUND(
                COUNT(*) FILTER (WHERE call_status = 'completed')::numeric
                / NULLIF(COUNT(*), 0) * 100, 1
            )                                                   AS completion_rate,
            ROUND(AVG(duration_seconds) FILTER
                  (WHERE call_status = 'completed'))::int       AS avg_duration_sec
        FROM call_sessions
        WHERE started_at >= $1
    """, since)

    payments = await db.fetchval("""
        SELECT COUNT(*) FROM call_outcomes co
        JOIN call_sessions cs ON cs.id = co.call_session_id
        WHERE co.outcome_type = 'payment_made'
          AND cs.started_at >= $1
    """, since)

    revenue = await db.fetchval("""
        SELECT COALESCE(SUM(s.plan_price), 0)
        FROM subscription_links sl
        JOIN subscriptions s ON s.id = sl.subscription_id
        JOIN call_sessions cs ON cs.id = sl.call_session_id
        WHERE sl.payment_status = 'paid'
          AND cs.started_at >= $1
    """, since)

    pending_fu = await db.fetchval("""
        SELECT COUNT(*) FROM follow_ups
        WHERE status = 'pending' AND created_at >= $1
    """, since)

    active_subs = await db.fetchval("""
        SELECT COUNT(*) FROM subscriptions WHERE status = 'active'
    """)

    mcp_row = await db.fetchrow("""
        SELECT
            COUNT(*)                                       AS total,
            ROUND(
                COUNT(*) FILTER (WHERE success)::numeric
                / NULLIF(COUNT(*), 0) * 100, 1
            )                                              AS success_rate,
            ROUND(AVG(duration_ms))::int                   AS avg_ms
        FROM mcp_tool_calls mc
        JOIN call_sessions cs ON cs.id = mc.call_session_id
        WHERE cs.started_at >= $1
    """, since)

    transcripts = await db.fetchval("""
        SELECT COUNT(*) FROM conversation_transcripts ct
        JOIN call_sessions cs ON cs.id = ct.call_session_id
        WHERE cs.started_at >= $1
    """, since)

    dur = row["avg_duration_sec"] or 0
    total = row["total_calls"] or 0

    return {
        "total_calls":          total,
        "completed_calls":      row["completed_calls"] or 0,
        "completion_rate":      float(row["completion_rate"] or 0),
        "payments_received":    payments or 0,
        "revenue_inr":          float(revenue or 0),
        "pending_follow_ups":   pending_fu or 0,
        "active_subscriptions": active_subs or 0,
        "avg_duration_sec":     dur,
        "avg_duration_str":     _fmt_duration(dur),
        "mcp_calls":            mcp_row["total"] or 0,
        "mcp_success_rate":     float(mcp_row["success_rate"] or 0),
        "transcripts_saved":    transcripts or 0,
        "range":                range_,
        "source":               "db",
        "no_data":              total == 0,
    }


# ── call volume chart ──────────────────────────────────────────────────────

async def get_call_volume(range_: str = "1d") -> dict:
    since = _since(range_)

    if range_ == "1d":
        rows = await db.fetch("""
            SELECT date_part('hour', started_at AT TIME ZONE 'Asia/Kolkata') AS bucket,
                   COUNT(*) AS cnt
            FROM call_sessions
            WHERE started_at >= $1
            GROUP BY 1 ORDER BY 1
        """, since)
        labels = [f"{h:02d}:00" for h in range(24)]
        bucket_map = {int(r["bucket"]): r["cnt"] for r in rows}
        data = [bucket_map.get(h, 0) for h in range(24)]

    elif range_ == "7d":
        rows = await db.fetch("""
            SELECT TO_CHAR(started_at AT TIME ZONE 'Asia/Kolkata', 'Dy') AS bucket,
                   COUNT(*) AS cnt
            FROM call_sessions
            WHERE started_at >= $1
            GROUP BY date_trunc('day', started_at AT TIME ZONE 'Asia/Kolkata'),
                     TO_CHAR(started_at AT TIME ZONE 'Asia/Kolkata', 'Dy')
            ORDER BY date_trunc('day', started_at AT TIME ZONE 'Asia/Kolkata')
        """, since)
        labels = [r["bucket"] for r in rows]
        data   = [r["cnt"] for r in rows]

    else:  # 30d — weekly buckets
        rows = await db.fetch("""
            SELECT 'Week ' || CEIL(
                       date_part('day',
                           started_at AT TIME ZONE 'Asia/Kolkata'
                           - $1::timestamptz AT TIME ZONE 'Asia/Kolkata'
                       ) / 7.0
                   )::int AS bucket,
                   COUNT(*) AS cnt
            FROM call_sessions
            WHERE started_at >= $1
            GROUP BY 1 ORDER BY 1
        """, since)
        labels = [r["bucket"] for r in rows]
        data   = [r["cnt"] for r in rows]

    return {
        "labels":  labels,
        "data":    data,
        "range":   range_,
        "source":  "db",
        "no_data": not any(data),
    }


# ── agent cards ────────────────────────────────────────────────────────────

async def get_agents(range_: str = "1d") -> list:
    since = _since(range_)

    COLOR_MAP = {
        "new_database":      {"color": "#1D9E75", "color_key": "teal"},
        "existing_database": {"color": "#378ADD", "color_key": "blue"},
        "implementation":    {"color": "#7F77DD", "color_key": "purple"},
        "renewal_reminder":  {"color": "#EF9F27", "color_key": "amber"},
    }
    SUBTITLE_MAP = {
        "new_database":      "Cold outbound · new leads",
        "existing_database": "Verification calls",
        "implementation":    "Activation confirmation",
        "renewal_reminder":  "Expiry-driven outbound",
    }
    STATS_DEF = {
        "new_database":      [("interested",    "Links sent", "teal"),
                              ("payment_made",  "Paid",       "teal"),
                              ("no_response",   "Follow-up",  "amber")],
        "existing_database": [("verified",      "Verified",   "blue"),
                              ("not_reachable", "Callback",   "amber"),
                              ("escalated",     "Escalated",  "red")],
        "implementation":    [("confirmed",     "Confirmed",  "purple"),
                              ("pending",       "Pending",    "amber"),
                              ("issue_raised",  "Tickets",    "red")],
        "renewal_reminder":  [("renewed",       "Renewed",    "amber"),
                              ("future_follow_up","Follow-up","gray"),
                              ("declined",      "Churned",    "red")],
    }

    agents = await db.fetch("""
        SELECT at.id, at.code, at.name,
               COUNT(cs.id) AS total_calls
        FROM agent_types at
        LEFT JOIN call_sessions cs
               ON cs.agent_type_id = at.id AND cs.started_at >= $1
        GROUP BY at.id, at.code, at.name
        ORDER BY at.id
    """, since)

    outcome_rows = await db.fetch("""
        SELECT cs.agent_type_id, co.outcome_type, COUNT(*) AS cnt
        FROM call_outcomes co
        JOIN call_sessions cs ON cs.id = co.call_session_id
        WHERE cs.started_at >= $1
        GROUP BY 1, 2
    """, since)

    from collections import defaultdict
    outcome_map: dict = defaultdict(dict)
    for r in outcome_rows:
        outcome_map[r["agent_type_id"]][r["outcome_type"]] = r["cnt"]

    outcome_list_map: dict = defaultdict(list)
    for r in outcome_rows:
        outcome_list_map[r["agent_type_id"]].append({
            "label": r["outcome_type"].replace("_", " ").title(),
            "count": r["cnt"],
        })

    result = []
    for a in agents:
        clr      = COLOR_MAP.get(a["code"], {"color": "#888780", "color_key": "gray"})
        outcomes = outcome_list_map.get(a["id"], [])
        total_out = sum(o["count"] for o in outcomes)

        stats_def = STATS_DEF.get(a["code"], [])
        out_counts = outcome_map.get(a["id"], {})
        stats = [
            {"label": lbl, "value": out_counts.get(otype, 0), "color_key": ck}
            for otype, lbl, ck in stats_def
        ]

        result.append({
            "id":          a["id"],
            "code":        a["code"],
            "name":        a["name"],
            "subtitle":    SUBTITLE_MAP.get(a["code"], ""),
            "color":       clr["color"],
            "color_key":   clr["color_key"],
            "total_calls": a["total_calls"],
            "outcomes": [
                {
                    "label": o["label"],
                    "count": o["count"],
                    "pct":   round(o["count"] / total_out * 100) if total_out else 0,
                    "color": clr["color"],
                }
                for o in outcomes
            ],
            "stats": stats,
        })

    return result


# ── outcome donut ──────────────────────────────────────────────────────────

async def get_outcomes(range_: str = "1d") -> list:
    since = _since(range_)

    COLORS = {
        "verified": "#1D9E75", "confirmed": "#1D9E75", "renewed": "#EF9F27",
        "interested": "#378ADD", "payment_made": "#1D9E75",
        "declined": "#E24B4A", "not_interested": "#E24B4A", "rejected": "#E24B4A",
        "no_response": "#888780", "not_reachable": "#888780",
        "escalated": "#E24B4A", "pending": "#EF9F27", "issue_raised": "#E24B4A",
        "future_follow_up": "#EF9F27",
    }

    rows = await db.fetch("""
        SELECT co.outcome_type, COUNT(*) AS cnt
        FROM call_outcomes co
        JOIN call_sessions cs ON cs.id = co.call_session_id
        WHERE cs.started_at >= $1
        GROUP BY 1
        ORDER BY cnt DESC
    """, since)

    if not rows:
        return []

    total = sum(r["cnt"] for r in rows)
    return [
        {
            "label":  r["outcome_type"].replace("_", " ").title(),
            "value":  r["cnt"],
            "pct":    round(r["cnt"] / total * 100) if total else 0,
            "color":  COLORS.get(r["outcome_type"], "#888780"),
            "source": "db",
        }
        for r in rows
    ]


# ── subscription funnel ────────────────────────────────────────────────────

async def get_funnel(range_: str = "1d") -> list:
    since = _since(range_)

    total = await db.fetchval(
        "SELECT COUNT(*) FROM call_sessions WHERE started_at >= $1", since)
    interested = await db.fetchval("""
        SELECT COUNT(*) FROM call_outcomes co
        JOIN call_sessions cs ON cs.id = co.call_session_id
        WHERE co.outcome_type IN ('interested','payment_made','renewed')
          AND cs.started_at >= $1
    """, since)
    link_sent = await db.fetchval("""
        SELECT COUNT(*) FROM subscription_links sl
        JOIN call_sessions cs ON cs.id = sl.call_session_id
        WHERE cs.started_at >= $1
    """, since)
    link_opened = await db.fetchval("""
        SELECT COUNT(*) FROM subscription_links sl
        JOIN call_sessions cs ON cs.id = sl.call_session_id
        WHERE sl.opened_at IS NOT NULL AND cs.started_at >= $1
    """, since)
    paid = await db.fetchval("""
        SELECT COUNT(*) FROM subscription_links sl
        JOIN call_sessions cs ON cs.id = sl.call_session_id
        WHERE sl.payment_status = 'paid' AND cs.started_at >= $1
    """, since)

    steps = [
        ("Calls made",   total or 0,        "#378ADD", "blue"),
        ("Interested",   interested or 0,   "#1D9E75", "teal"),
        ("Link sent",    link_sent or 0,    "#7F77DD", "purple"),
        ("Link opened",  link_opened or 0,  "#EF9F27", "amber"),
        ("Payment made", paid or 0,         "#1D9E75", "teal"),
    ]
    base = total or 1
    return [
        {
            "label":     l,
            "value":     v,
            "pct":       round(v / base * 100),
            "color":     c,
            "color_key": ck,
            "source":    "db",
        }
        for l, v, c, ck in steps
    ]


# ── follow-up queue ────────────────────────────────────────────────────────

async def get_follow_ups(range_: str = "1d") -> dict:
    since = _since(range_)
    rows = await db.fetch("""
        SELECT at.name AS agent, fu.reason,
               COUNT(*) AS cnt,
               at.code
        FROM follow_ups fu
        JOIN agent_types at ON at.id = fu.agent_type_id
        WHERE fu.status = 'pending'
          AND fu.created_at >= $1
        GROUP BY at.id, at.name, at.code, fu.reason
        ORDER BY cnt DESC
    """, since)

    COLOR_MAP = {
        "new_database":      {"color": "#1D9E75", "color_key": "teal"},
        "existing_database": {"color": "#378ADD", "color_key": "blue"},
        "implementation":    {"color": "#7F77DD", "color_key": "purple"},
        "renewal_reminder":  {"color": "#EF9F27", "color_key": "amber"},
    }

    if not rows:
        return {"total": 0, "items": [], "source": "db", "no_data": True}

    total = sum(r["cnt"] for r in rows)
    items = [
        {
            "agent":  r["agent"],
            "reason": r["reason"],
            "count":  r["cnt"],
            **COLOR_MAP.get(r["code"], {"color": "#888780", "color_key": "gray"}),
        }
        for r in rows
    ]
    return {"total": total, "items": items, "source": "db", "no_data": False}


# ── recent sessions ────────────────────────────────────────────────────────

async def get_sessions(range_: str = "1d", limit: int = 6) -> list:
    since = _since(range_)
    rows = await db.fetch("""
        SELECT cs.id, c.name AS customer_name,
               at.name AS agent, at.code AS agent_code,
               cs.call_status, cs.duration_seconds,
               co.outcome_type,
               cs.started_at
        FROM call_sessions cs
        JOIN customers c     ON c.id  = cs.customer_id
        JOIN agent_types at  ON at.id = cs.agent_type_id
        LEFT JOIN call_outcomes co ON co.call_session_id = cs.id
        WHERE cs.started_at >= $1
        ORDER BY cs.started_at DESC
        LIMIT $2
    """, since, limit)

    COLOR_MAP = {
        "new_database":      "teal",
        "existing_database": "blue",
        "implementation":    "purple",
        "renewal_reminder":  "amber",
    }
    STATUS_KEY = {"completed": "done", "no_answer": "pend", "failed": "fail",
                  "in_progress": "work", "initiated": "work", "ringing": "work", "busy": "pend"}

    if not rows:
        return []

    return [
        {
            "id":            str(r["id"]),
            "customer_name": r["customer_name"],
            "initials":      "".join(w[0] for w in r["customer_name"].split()[:2]).upper(),
            "agent":         r["agent"],
            "color_key":     COLOR_MAP.get(r["agent_code"], "gray"),
            "outcome":       r["outcome_type"].replace("_", " ").title() if r["outcome_type"] else "—",
            "outcome_key":   r["outcome_type"] or "none",
            "duration":      _fmt_duration(r["duration_seconds"]),
            "status":        r["call_status"].replace("_", " ").title(),
            "status_key":    STATUS_KEY.get(r["call_status"], "pend"),
            "started_at":    r["started_at"].isoformat(),
            "source":        "db",
        }
        for r in rows
    ]


# ── MCP tools ─────────────────────────────────────────────────────────────

async def get_mcp_tools(range_: str = "1d") -> dict:
    since = _since(range_)

    summary = await db.fetchrow("""
        SELECT COUNT(*)                                         AS total,
               ROUND(
                 COUNT(*) FILTER (WHERE mc.success)::numeric
                 / NULLIF(COUNT(*), 0) * 100, 1
               )                                               AS success_rate,
               ROUND(AVG(mc.duration_ms))::int                 AS avg_ms,
               COUNT(*) FILTER (WHERE NOT mc.success)          AS failures
        FROM mcp_tool_calls mc
        JOIN call_sessions cs ON cs.id = mc.call_session_id
        WHERE cs.started_at >= $1
    """, since)

    rows = await db.fetch("""
        SELECT mc.tool_name, COUNT(*) AS cnt,
               ROUND(AVG(mc.duration_ms))::int AS avg_ms
        FROM mcp_tool_calls mc
        JOIN call_sessions cs ON cs.id = mc.call_session_id
        WHERE cs.started_at >= $1
        GROUP BY mc.tool_name
        ORDER BY cnt DESC
    """, since)

    max_cnt = rows[0]["cnt"] if rows else 1
    COLORS = ["#378ADD", "#1D9E75", "#7F77DD", "#EF9F27",
              "#7F77DD", "#E24B4A", "#888780"]

    return {
        "total":        summary["total"] or 0,
        "success_rate": float(summary["success_rate"] or 0),
        "avg_ms":       summary["avg_ms"] or 0,
        "failures":     summary["failures"] or 0,
        "source":       "db",
        "no_data":      (summary["total"] or 0) == 0,
        "tools": [
            {
                "name":   r["tool_name"],
                "count":  r["cnt"],
                "avg_ms": r["avg_ms"],
                "pct":    round(r["cnt"] / max_cnt * 100),
                "color":  COLORS[i % len(COLORS)],
            }
            for i, r in enumerate(rows)
        ],
    }


# ── system health ──────────────────────────────────────────────────────────

async def get_health() -> dict:
    db_ok = await db.fetchval("SELECT 1") == 1
    return {
        "services": [
            {"name": "Plivo websocket", "icon": "phone",    "latency": "12ms", "status": "online",
             "status_key": "done"},
            {"name": "Gemini Live",     "icon": "brain",    "latency": "38ms", "status": "online",
             "status_key": "done"},
            {"name": "MCP server",      "icon": "cpu",      "latency": "5ms",  "status": "running",
             "status_key": "done"},
            {"name": "PostgreSQL",      "icon": "database", "latency": "3ms",
             "status": "connected" if db_ok else "error",
             "status_key": "done" if db_ok else "fail"},
            {"name": "Quart backend",   "icon": "server",   "latency": "—",    "status": "active",
             "status_key": "done"},
        ]
    }


# ── subscription status ────────────────────────────────────────────────────

async def get_sub_status(range_: str = "1d") -> dict:
    since = _since(range_)
    rows = await db.fetch("""
        SELECT status, COUNT(*) AS cnt
        FROM subscriptions
        WHERE created_at >= $1
        GROUP BY status
        ORDER BY cnt DESC
    """, since)
    COLOR_MAP = {"active": "#1D9E75", "pending": "#EF9F27",
                 "expired": "#E24B4A", "cancelled": "#888780", "suspended": "#888780"}

    if not rows:
        return {"labels": [], "data": [], "colors": [], "no_data": True}

    labels = [r["status"].title() for r in rows]
    data   = [r["cnt"] for r in rows]
    colors = [COLOR_MAP.get(r["status"], "#888780") for r in rows]
    return {"labels": labels, "data": data, "colors": colors, "no_data": False}


# ══════════════════════════════════════════════════════════════════════════
#  CONVERSATION / TEAMS  section
# ══════════════════════════════════════════════════════════════════════════

async def get_conversations(range_: str = "1d", limit: int = 20, offset: int = 0) -> dict:
    since = _since(range_)

    rows = await db.fetch("""
        SELECT
            cs.id,
            c.name           AS customer_name,
            c.phone          AS customer_phone,
            at.name          AS agent_name,
            at.code          AS agent_code,
            cs.call_status,
            cs.duration_seconds,
            cs.started_at,
            cs.ended_at,
            co.outcome_type,
            COUNT(ct.id)     AS message_count
        FROM call_sessions cs
        JOIN customers   c   ON c.id  = cs.customer_id
        JOIN agent_types at  ON at.id = cs.agent_type_id
        LEFT JOIN call_outcomes co   ON co.call_session_id = cs.id
        LEFT JOIN conversation_transcripts ct ON ct.call_session_id = cs.id
        WHERE cs.started_at >= $1
        GROUP BY cs.id, c.name, c.phone, at.name, at.code,
                 cs.call_status, cs.duration_seconds, cs.started_at, cs.ended_at,
                 co.outcome_type
        ORDER BY cs.started_at DESC
        LIMIT $2 OFFSET $3
    """, since, limit, offset)

    total = await db.fetchval("""
        SELECT COUNT(*) FROM call_sessions WHERE started_at >= $1
    """, since)

    COLOR_MAP = {
        "new_database":      "teal",
        "existing_database": "blue",
        "implementation":    "purple",
        "renewal_reminder":  "amber",
    }

    items = []
    for r in rows:
        preview = await db.fetch("""
            SELECT role, content, ts FROM conversation_transcripts
            WHERE call_session_id = $1
            ORDER BY ts
            LIMIT 1
        """, r["id"])

        items.append({
            "session_id":     str(r["id"]),
            "customer_name":  r["customer_name"],
            "customer_phone": r["customer_phone"],
            "initials":       "".join(w[0] for w in r["customer_name"].split()[:2]).upper(),
            "agent_name":     r["agent_name"],
            "agent_code":     r["agent_code"],
            "color_key":      COLOR_MAP.get(r["agent_code"], "gray"),
            "call_status":    r["call_status"],
            "duration":       _fmt_duration(r["duration_seconds"]),
            "started_at":     r["started_at"].isoformat(),
            "ended_at":       r["ended_at"].isoformat() if r["ended_at"] else None,
            "outcome":        r["outcome_type"].replace("_", " ").title() if r["outcome_type"] else "—",
            "message_count":  r["message_count"],
            "preview":        preview[0]["content"][:80] + "…" if preview else "",
        })

    return {
        "total":   total or 0,
        "limit":   limit,
        "offset":  offset,
        "range":   range_,
        "items":   items,
        "no_data": (total or 0) == 0,
    }


async def get_conversation_detail(session_id: str) -> dict:
    sid = session_id

    session = await db.fetchrow("""
        SELECT
            cs.id, cs.call_status, cs.started_at, cs.ended_at,
            cs.duration_seconds, cs.plivo_call_id, cs.gemini_session_id,
            c.id AS customer_id, c.name AS customer_name, c.phone AS customer_phone,
            c.email AS customer_email,
            at.name AS agent_name, at.code AS agent_code,
            co.outcome_type, co.notes AS outcome_notes
        FROM call_sessions cs
        JOIN customers   c   ON c.id  = cs.customer_id
        JOIN agent_types at  ON at.id = cs.agent_type_id
        LEFT JOIN call_outcomes co ON co.call_session_id = cs.id
        WHERE cs.id = $1::uuid
    """, sid)

    if not session:
        return {}

    transcript = await db.fetch("""
        SELECT role, content, ts
        FROM conversation_transcripts
        WHERE call_session_id = $1::uuid
        ORDER BY ts ASC
    """, sid)

    mcp_calls = await db.fetch("""
        SELECT tool_name, input_json, output_json, duration_ms, success, called_at
        FROM mcp_tool_calls
        WHERE call_session_id = $1::uuid
        ORDER BY called_at ASC
    """, sid)

    follow_up = await db.fetchrow("""
        SELECT scheduled_at, reason, status
        FROM follow_ups
        WHERE call_session_id = $1::uuid
        LIMIT 1
    """, sid)

    sub_link = await db.fetchrow("""
        SELECT sl.link_url, sl.payment_status, sl.sent_at, sl.opened_at, sl.payment_made_at,
               s.plan_name, s.plan_price
        FROM subscription_links sl
        JOIN subscriptions s ON s.id = sl.subscription_id
        WHERE sl.call_session_id = $1::uuid
        LIMIT 1
    """, sid)

    return {
        "session": {
            "id":                str(session["id"]),
            "call_status":       session["call_status"],
            "started_at":        session["started_at"].isoformat(),
            "ended_at":          session["ended_at"].isoformat() if session["ended_at"] else None,
            "duration":          _fmt_duration(session["duration_seconds"]),
            "plivo_call_id":     session["plivo_call_id"],
            "gemini_session_id": session["gemini_session_id"],
        },
        "customer": {
            "id":    str(session["customer_id"]),
            "name":  session["customer_name"],
            "phone": session["customer_phone"],
            "email": session["customer_email"],
        },
        "agent": {
            "name": session["agent_name"],
            "code": session["agent_code"],
        },
        "outcome": {
            "type":  session["outcome_type"],
            "notes": session["outcome_notes"],
        } if session["outcome_type"] else None,
        "transcript": [
            {
                "role":    r["role"],
                "content": r["content"],
                "ts":      r["ts"].isoformat(),
            }
            for r in transcript
        ],
        "mcp_calls": [
            {
                "tool":        m["tool_name"],
                "input":       m["input_json"],
                "output":      m["output_json"],
                "duration_ms": m["duration_ms"],
                "success":     m["success"],
                "called_at":   m["called_at"].isoformat(),
            }
            for m in mcp_calls
        ],
        "follow_up": {
            "scheduled_at": follow_up["scheduled_at"].isoformat(),
            "reason":       follow_up["reason"],
            "status":       follow_up["status"],
        } if follow_up else None,
        "subscription_link": {
            "url":            sub_link["link_url"],
            "payment_status": sub_link["payment_status"],
            "plan_name":      sub_link["plan_name"],
            "plan_price":     float(sub_link["plan_price"]),
            "sent_at":        sub_link["sent_at"].isoformat() if sub_link["sent_at"] else None,
            "opened_at":      sub_link["opened_at"].isoformat() if sub_link["opened_at"] else None,
            "paid_at":        sub_link["payment_made_at"].isoformat() if sub_link["payment_made_at"] else None,
        } if sub_link else None,
    }


async def get_team_stats(range_: str = "1d") -> list:
    since = _since(range_)

    rows = await db.fetch("""
        SELECT
            at.id, at.code, at.name,
            COUNT(cs.id)                                                AS total_calls,
            COUNT(cs.id) FILTER (WHERE cs.call_status = 'completed')   AS completed,
            COUNT(cs.id) FILTER (WHERE cs.call_status = 'no_answer')   AS no_answer,
            COUNT(cs.id) FILTER (WHERE cs.call_status = 'failed')      AS failed,
            ROUND(AVG(cs.duration_seconds)
                  FILTER (WHERE cs.call_status='completed'))::int       AS avg_duration_sec,
            ROUND(
                COUNT(cs.id) FILTER (WHERE cs.call_status='completed')::numeric
                / NULLIF(COUNT(cs.id), 0) * 100, 1
            )                                                           AS completion_rate
        FROM agent_types at
        LEFT JOIN call_sessions cs
               ON cs.agent_type_id = at.id AND cs.started_at >= $1
        GROUP BY at.id, at.code, at.name
        ORDER BY at.id
    """, since)

    outcome_rows = await db.fetch("""
        SELECT cs.agent_type_id, co.outcome_type, COUNT(*) AS cnt
        FROM call_outcomes co
        JOIN call_sessions cs ON cs.id = co.call_session_id
        WHERE cs.started_at >= $1
        GROUP BY 1, 2
    """, since)

    mcp_rows = await db.fetch("""
        SELECT cs.agent_type_id,
               COUNT(*)                                      AS total_mcp,
               COUNT(*) FILTER (WHERE mc.success)            AS success_mcp,
               ROUND(AVG(mc.duration_ms))::int               AS avg_mcp_ms
        FROM mcp_tool_calls mc
        JOIN call_sessions cs ON cs.id = mc.call_session_id
        WHERE cs.started_at >= $1
        GROUP BY cs.agent_type_id
    """, since)

    from collections import defaultdict
    out_map: dict = defaultdict(list)
    for r in outcome_rows:
        out_map[r["agent_type_id"]].append({
            "type":  r["outcome_type"],
            "label": r["outcome_type"].replace("_", " ").title(),
            "count": r["cnt"],
        })
    mcp_map = {r["agent_type_id"]: dict(r) for r in mcp_rows}

    COLOR_MAP = {
        "new_database":      {"color": "#1D9E75", "color_key": "teal"},
        "existing_database": {"color": "#378ADD", "color_key": "blue"},
        "implementation":    {"color": "#7F77DD", "color_key": "purple"},
        "renewal_reminder":  {"color": "#EF9F27", "color_key": "amber"},
    }

    result = []
    for r in rows:
        clr = COLOR_MAP.get(r["code"], {"color": "#888780", "color_key": "gray"})
        mcp = mcp_map.get(r["id"], {})
        result.append({
            "id":              r["id"],
            "code":            r["code"],
            "name":            r["name"],
            **clr,
            "total_calls":     r["total_calls"],
            "completed":       r["completed"],
            "no_answer":       r["no_answer"],
            "failed":          r["failed"],
            "completion_rate": float(r["completion_rate"] or 0),
            "avg_duration":    _fmt_duration(r["avg_duration_sec"]),
            "outcomes":        out_map.get(r["id"], []),
            "mcp": {
                "total":   mcp.get("total_mcp", 0),
                "success": mcp.get("success_mcp", 0),
                "avg_ms":  mcp.get("avg_mcp_ms", 0),
            },
        })
    return result
