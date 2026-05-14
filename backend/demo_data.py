import random
from datetime import datetime, timedelta, timezone

random.seed(42)

# ── Multipliers per range ──────────────────────────────────────────────────
MULT = {"1d": 1, "7d": 7, "30d": 30}

# ── Hourly call volume (base = today) ─────────────────────────────────────
BASE_VOLUME = [2,1,0,1,2,4,8,14,18,22,28,35,29,24,32,38,27,19,14,10,7,5,3,2]

def _scale(v, m): return max(0, round(v * m * (0.80 + random.uniform(0, 0.40))))

def get_call_volume(range_: str = "1d"):
    m = MULT.get(range_, 1)
    if range_ == "1d":
        labels = [f"{h:02d}:00" for h in range(24)]
        data   = [*BASE_VOLUME]
    elif range_ == "7d":
        labels = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
        data   = [_scale(sum(BASE_VOLUME), 1) for _ in labels]
    else:
        labels = [f"Week {i+1}" for i in range(4)]
        data   = [_scale(sum(BASE_VOLUME) * 7, 1) for _ in labels]
    return {"labels": labels, "data": data, "range": range_}

# ── KPI / Dashboard summary ────────────────────────────────────────────────
def get_dashboard(range_: str = "1d"):
    m = MULT.get(range_, 1)
    return {
        "total_calls":        247 * m,
        "completed_calls":    189 * m,
        "completion_rate":    76.5,
        "payments_received":  38  * m,
        "revenue_inr":        round(114000 * m),
        "pending_follow_ups": 72  if range_ == "1d" else (314 if range_ == "7d" else 1102),
        "new_follow_ups":     6   * m,
        "active_subscriptions": 214,
        "avg_duration_sec":   252,
        "avg_duration_str":   "4:12",
        "mcp_calls":          1340 * m,
        "mcp_success_rate":   98.4,
        "transcripts_saved":  18920 * m,
        "range": range_,
    }

# ── 4 Agent cards ──────────────────────────────────────────────────────────
BASE_AGENTS = [
    {
        "id": 1,
        "code": "new_database",
        "name": "New Database",
        "subtitle": "Cold outbound · new leads",
        "color": "#1D9E75",
        "color_key": "teal",
        "total_calls": 84,
        "outcomes": [
            {"label": "Interested",     "pct": 42, "color": "#1D9E75"},
            {"label": "Not interested", "pct": 31, "color": "#E24B4A"},
            {"label": "No response",    "pct": 27, "color": "#888780"},
        ],
        "stats": [
            {"label": "Links sent", "value": 29, "color_key": "teal"},
            {"label": "Paid",       "value": 18, "color_key": "teal"},
            {"label": "Follow-up",  "value": 41, "color_key": "amber"},
        ],
    },
    {
        "id": 2,
        "code": "existing_database",
        "name": "Existing Database",
        "subtitle": "Verification calls",
        "color": "#378ADD",
        "color_key": "blue",
        "total_calls": 82,
        "outcomes": [
            {"label": "Verified",      "pct": 74, "color": "#378ADD"},
            {"label": "Not reachable", "pct": 16, "color": "#888780"},
            {"label": "Escalated",     "pct": 10, "color": "#E24B4A"},
        ],
        "stats": [
            {"label": "Verified",   "value": 61, "color_key": "blue"},
            {"label": "Callback",   "value": 13, "color_key": "amber"},
            {"label": "Escalated",  "value": 8,  "color_key": "red"},
        ],
    },
    {
        "id": 3,
        "code": "implementation",
        "name": "Implementation",
        "subtitle": "Activation confirmation",
        "color": "#7F77DD",
        "color_key": "purple",
        "total_calls": 42,
        "outcomes": [
            {"label": "Confirmed",    "pct": 81, "color": "#7F77DD"},
            {"label": "Pending",      "pct": 12, "color": "#EF9F27"},
            {"label": "Issue raised", "pct": 7,  "color": "#E24B4A"},
        ],
        "stats": [
            {"label": "Confirmed", "value": 34, "color_key": "purple"},
            {"label": "Pending",   "value": 5,  "color_key": "amber"},
            {"label": "Tickets",   "value": 3,  "color_key": "red"},
        ],
    },
    {
        "id": 4,
        "code": "renewal_reminder",
        "name": "Renewal Reminder",
        "subtitle": "Expiry-driven outbound",
        "color": "#EF9F27",
        "color_key": "amber",
        "total_calls": 39,
        "outcomes": [
            {"label": "Renewed",     "pct": 67, "color": "#EF9F27"},
            {"label": "Declined",    "pct": 22, "color": "#E24B4A"},
            {"label": "No response", "pct": 11, "color": "#888780"},
        ],
        "stats": [
            {"label": "Renewed",   "value": 21, "color_key": "amber"},
            {"label": "Follow-up", "value": 7,  "color_key": "gray"},
            {"label": "Churned",   "value": 7,  "color_key": "red"},
        ],
    },
]

def get_agents(range_: str = "1d"):
    m = MULT.get(range_, 1)
    agents = []
    for a in BASE_AGENTS:
        ag = dict(a)
        ag["total_calls"] = a["total_calls"] * m
        ag["stats"] = [
            {**s, "value": s["value"] * m}
            for s in a["stats"]
        ]
        agents.append(ag)
    return agents

# ── Outcome breakdown (donut) ──────────────────────────────────────────────
def get_outcomes(range_: str = "1d"):
    m = MULT.get(range_, 1)
    base = [
        {"label": "Verified / confirmed", "value": 87,  "color": "#1D9E75"},
        {"label": "Interested",           "value": 67,  "color": "#378ADD"},
        {"label": "Renewed",              "value": 27,  "color": "#EF9F27"},
        {"label": "Declined / rejected",  "value": 35,  "color": "#E24B4A"},
        {"label": "No response",          "value": 31,  "color": "#888780"},
    ]
    total = sum(b["value"] for b in base)
    return [
        {**b, "value": b["value"] * m, "pct": round(b["value"] / total * 100)}
        for b in base
    ]

# ── Subscription funnel ────────────────────────────────────────────────────
def get_funnel(range_: str = "1d"):
    m = MULT.get(range_, 1)
    steps = [
        {"label": "Calls made",   "value": 247, "color": "#378ADD", "color_key": "blue"},
        {"label": "Interested",   "value": 160, "color": "#1D9E75", "color_key": "teal"},
        {"label": "Link sent",    "value": 104, "color": "#7F77DD", "color_key": "purple"},
        {"label": "Link opened",  "value": 72,  "color": "#EF9F27", "color_key": "amber"},
        {"label": "Payment made", "value": 38,  "color": "#1D9E75", "color_key": "teal"},
    ]
    base_val = steps[0]["value"] * m
    return [
        {**s, "value": s["value"] * m, "pct": round(s["value"] / 247 * 100)}
        for s in steps
    ]

# ── Follow-up queue ────────────────────────────────────────────────────────
def get_follow_ups():
    return {
        "total": 72,
        "items": [
            {"agent": "New Database",    "reason": "3-month reconnect",  "count": 41, "color": "#1D9E75", "color_key": "teal"},
            {"agent": "Existing DB",     "reason": "Callback requested", "count": 13, "color": "#378ADD", "color_key": "blue"},
            {"agent": "Renewal",         "reason": "Future follow-up",   "count": 7,  "color": "#EF9F27", "color_key": "amber"},
            {"agent": "Implementation",  "reason": "Still pending",      "count": 5,  "color": "#7F77DD", "color_key": "purple"},
            {"agent": "New DB",          "reason": "Payment assistance", "count": 6,  "color": "#1D9E75", "color_key": "teal"},
        ]
    }

# ── Recent call sessions ───────────────────────────────────────────────────
ALL_SESSIONS = [
    {"id":"cs-001","customer_name":"Rahul Anand",     "initials":"RA","agent":"New DB",  "color_key":"teal",  "outcome":"Payment made",  "outcome_key":"payment_made","duration":"3m 42s","status":"completed","status_key":"done"},
    {"id":"cs-002","customer_name":"Priya Kumar",     "initials":"PK","agent":"Existing","color_key":"blue",  "outcome":"Verified",       "outcome_key":"verified",    "duration":"1m 58s","status":"completed","status_key":"done"},
    {"id":"cs-003","customer_name":"Mohan Sharma",    "initials":"MS","agent":"Renewal", "color_key":"red",   "outcome":"Declined",       "outcome_key":"declined",    "duration":"2m 11s","status":"completed","status_key":"done"},
    {"id":"cs-004","customer_name":"Nisha Rao",       "initials":"NR","agent":"Impl.",   "color_key":"purple","outcome":"Confirmed",       "outcome_key":"confirmed",   "duration":"4m 07s","status":"completed","status_key":"done"},
    {"id":"cs-005","customer_name":"Suresh Krishnan", "initials":"SK","agent":"New DB",  "color_key":"teal",  "outcome":"Not interested", "outcome_key":"not_interested","duration":"1m 34s","status":"follow-up","status_key":"pend"},
    {"id":"cs-006","customer_name":"Anita Mishra",    "initials":"AM","agent":"Existing","color_key":"blue",  "outcome":"In progress",    "outcome_key":"in_progress", "duration":"—",     "status":"active",   "status_key":"work"},
    {"id":"cs-007","customer_name":"Vikram Patel",    "initials":"VP","agent":"Renewal", "color_key":"amber", "outcome":"Renewed",        "outcome_key":"renewed",     "duration":"5m 03s","status":"completed","status_key":"done"},
    {"id":"cs-008","customer_name":"Deepa Iyer",      "initials":"DI","agent":"New DB",  "color_key":"teal",  "outcome":"Interested",     "outcome_key":"interested",  "duration":"3m 19s","status":"follow-up","status_key":"pend"},
    {"id":"cs-009","customer_name":"Arjun Mehta",     "initials":"AR","agent":"Impl.",   "color_key":"purple","outcome":"Issue raised",    "outcome_key":"issue_raised","duration":"6m 44s","status":"escalated","status_key":"fail"},
    {"id":"cs-010","customer_name":"Kavya Reddy",     "initials":"KR","agent":"Existing","color_key":"blue",  "outcome":"Verified",       "outcome_key":"verified",    "duration":"2m 02s","status":"completed","status_key":"done"},
]

def get_sessions(limit: int = 6):
    return ALL_SESSIONS[:limit]

# ── MCP tool calls ────────────────────────────────────────────────────────
def get_mcp_tools(range_: str = "1d"):
    m = MULT.get(range_, 1)
    base = [
        {"name":"lookup_customer",    "count":387,"color":"#378ADD","max":387},
        {"name":"get_subscription",   "count":279,"color":"#1D9E75","max":387},
        {"name":"create_follow_up",   "count":231,"color":"#7F77DD","max":387},
        {"name":"send_payment_link",  "count":178,"color":"#EF9F27","max":387},
        {"name":"update_call_outcome","count":154,"color":"#7F77DD","max":387},
        {"name":"check_expiry",       "count":84, "color":"#E24B4A","max":387},
        {"name":"verify_customer",    "count":27, "color":"#888780","max":387},
    ]
    total = sum(b["count"] for b in base)
    return {
        "total": total * m,
        "success_rate": 98.4,
        "avg_ms": 42,
        "failures": 21 * m,
        "tools": [
            {**b, "count": b["count"]*m, "pct": round(b["count"]/387*100)}
            for b in base
        ]
    }

# ── System health ─────────────────────────────────────────────────────────
def get_health():
    return {
        "services": [
            {"name":"Plivo websocket", "icon":"phone",    "latency":"12ms", "status":"online",    "status_key":"done"},
            {"name":"Gemini Live",     "icon":"brain",    "latency":"38ms", "status":"online",    "status_key":"done"},
            {"name":"MCP server",      "icon":"cpu",      "latency":"5ms",  "status":"running",   "status_key":"done"},
            {"name":"PostgreSQL",      "icon":"database", "latency":"3ms",  "status":"connected", "status_key":"done"},
            {"name":"Quart backend",   "icon":"server",   "latency":"—",    "status":"active",    "status_key":"done"},
        ]
    }

# ── Subscription status split ─────────────────────────────────────────────
def get_sub_status():
    return {
        "labels": ["Active","Pending","Expired","Cancelled"],
        "data":   [214, 48, 31, 12],
        "colors": ["#1D9E75","#EF9F27","#E24B4A","#888780"],
    }
