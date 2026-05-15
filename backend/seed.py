"""
Seed the DB with realistic test data.
  cd backend && venv/bin/python3 seed.py
"""
import asyncio, os, uuid, random
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import asyncpg

load_dotenv()
random.seed(99)
NOW = datetime.now(timezone.utc)

CUSTOMERS = [
    ("Rahul Anand",     "+919876543210", "rahul@example.com",  "new_database",      "active"),
    ("Priya Kumar",     "+919876543211", "priya@example.com",  "existing_database", "active"),
    ("Mohan Sharma",    "+919876543212", None,                  "new_database",      "prospect"),
    ("Nisha Rao",       "+919876543213", "nisha@example.com",  "existing_database", "active"),
    ("Suresh Krishnan", "+919876543214", None,                  "new_database",      "inactive"),
    ("Anita Mishra",    "+919876543215", "anita@example.com",  "existing_database", "active"),
    ("Vikram Patel",    "+919876543216", "vikram@example.com", "new_database",      "active"),
    ("Deepa Iyer",      "+919876543217", "deepa@example.com",  "existing_database", "active"),
    ("Arjun Mehta",     "+919876543218", None,                  "new_database",      "churned"),
    ("Kavya Reddy",     "+919876543219", "kavya@example.com",  "existing_database", "active"),
    ("Amit Singh",      "+919876543220", "amit@example.com",   "new_database",      "prospect"),
    ("Ritu Verma",      "+919876543221", None,                  "existing_database", "active"),
]

PLANS = [
    ("Basic Monthly",    299.00),
    ("Standard Monthly", 499.00),
    ("Premium Monthly",  999.00),
    ("Annual Plan",     4999.00),
]

AGENT_CODE_MAP = {1: "new_database", 2: "existing_database", 3: "implementation", 4: "renewal_reminder"}

OUTCOME_MAP = {
    1: ["interested", "not_interested", "no_response", "payment_made"],
    2: ["verified", "not_reachable", "escalated"],
    3: ["confirmed", "pending", "issue_raised"],
    4: ["renewed", "declined", "future_follow_up"],
}

MCP_TOOLS = ["lookup_customer", "get_subscription", "create_follow_up",
             "send_payment_link", "update_call_outcome", "check_expiry", "verify_customer"]

CONVO = {
    "new_database": [
        ("assistant", "Namaste! Am I speaking with {name}?"),
        ("user",      "Haan, main {name} bol raha hoon."),
        ("assistant", "Main aapko Hindustan Times ke digital subscription ke baare mein bata raha hoon. Kya aap interested hain?"),
        ("user",      "Haan, thoda batao."),
        ("assistant", "Hamare Basic plan mein daily e-paper aur news alerts milte hain sirf ₹299 per month mein."),
        ("user",      "Theek hai, payment link bhejo."),
        ("assistant", "Bilkul! Main abhi link bhejta hoon. Ek minute."),
    ],
    "existing_database": [
        ("assistant", "Hello, {name} ji! Main aapka subscription verify karna chahta hoon."),
        ("user",      "Haan boliye."),
        ("assistant", "Kya aap abhi bhi registered number use kar rahe hain?"),
        ("user",      "Haan, same number hai."),
        ("assistant", "Verification complete hua. Aapka account active hai. Koi issue?"),
        ("user",      "Nahi, sab theek hai."),
        ("assistant", "Thank you! Koi zaroorat ho toh humein call karein."),
    ],
    "renewal_reminder": [
        ("assistant", "Namaste {name} ji! Aapka subscription 7 din mein expire ho raha hai."),
        ("user",      "Achha, kya offer hai renewal pe?"),
        ("assistant", "Annual plan pe 20% discount mil raha hai — sirf ₹3999."),
        ("user",      "Theek hai, mujhe link bhejo."),
        ("assistant", "Zaroor! Payment link aapke registered number pe ja raha hai."),
    ],
    "implementation": [
        ("assistant", "Hi {name}! Aapka subscription activate hua. Sab theek chal raha hai?"),
        ("user",      "Haan, app download kar li. Login ho gaya."),
        ("assistant", "Bahut achha! Koi technical issue toh nahi?"),
        ("user",      "Nahi, sab smooth hai."),
        ("assistant", "Great! Enjoy karo aapka subscription."),
    ],
}


async def seed():
    conn = await asyncpg.connect(
        host=os.getenv("DB_HOST"), port=int(os.getenv("DB_PORT", 5432)),
        user=os.getenv("DB_USER"), password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )

    print("Truncating old data...")
    await conn.execute("""
        TRUNCATE customers, subscriptions, call_sessions, call_outcomes,
                 conversation_transcripts, follow_ups, mcp_tool_calls,
                 subscription_links RESTART IDENTITY CASCADE
    """)

    # ── customers ────────────────────────────────────────────────────────
    cust_ids = []
    for name, phone, email, source, status in CUSTOMERS:
        cid = uuid.uuid4()
        cust_ids.append((cid, name, source))
        ts = NOW - timedelta(days=random.randint(10, 120))
        await conn.execute("""
            INSERT INTO customers (id, name, phone, email, source_type, status, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5::customer_source,$6::customer_status,$7,$7)
        """, cid, name, phone, email, source, status, ts)
    print(f"  {len(cust_ids)} customers")

    # ── subscriptions ─────────────────────────────────────────────────────
    sub_map = {}
    for cid, name, _ in cust_ids[:9]:
        sid = uuid.uuid4()
        sub_map[cid] = sid
        plan, price = random.choice(PLANS)
        status = random.choice(["active", "active", "active", "pending", "expired"])
        act = NOW - timedelta(days=random.randint(5, 90))
        exp = act + timedelta(days=30 if "Monthly" in plan else 365)
        await conn.execute("""
            INSERT INTO subscriptions
              (id, customer_id, plan_name, plan_price, status, activated_at, expires_at, created_at, updated_at)
            VALUES ($1,$2,$3,$4,$5::subscription_status,$6,$7,$6,$6)
        """, sid, cid, plan, price, status, act, exp)
    print(f"  {len(sub_map)} subscriptions")

    # ── call sessions (spread over last 30 days) ───────────────────────────
    session_count = 0
    for _ in range(50):
        cid, name, _ = random.choice(cust_ids)
        agent_id = random.choice([1, 2, 3, 4])
        agent_code = AGENT_CODE_MAP[agent_id]

        sess_id = uuid.uuid4()
        started = NOW - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        dur = random.randint(60, 420)
        ended = started + timedelta(seconds=dur)
        status = random.choice(["completed", "completed", "completed", "no_answer", "failed"])

        await conn.execute("""
            INSERT INTO call_sessions
              (id, customer_id, agent_type_id, call_status, started_at, ended_at,
               plivo_call_id, created_at)
            VALUES ($1,$2,$3,$4::call_status,$5,$6,$7,$5)
        """, sess_id, cid, agent_id, status, started, ended,
             f"PLV-{sess_id.hex[:8].upper()}")
        session_count += 1

        # ── transcript ────────────────────────────────────────────────────
        lines = CONVO[agent_code]
        step = dur // max(len(lines), 1)
        for j, (role, tmpl) in enumerate(lines):
            await conn.execute("""
                INSERT INTO conversation_transcripts (id, call_session_id, role, content, ts)
                VALUES ($1,$2,$3::transcript_role,$4,$5)
            """, uuid.uuid4(), sess_id, role, tmpl.format(name=name),
                 started + timedelta(seconds=j * step))

        if status != "completed":
            continue

        # ── outcome ───────────────────────────────────────────────────────
        outcome = random.choice(OUTCOME_MAP[agent_id])
        await conn.execute("""
            INSERT INTO call_outcomes (id, call_session_id, outcome_type, notes, created_at)
            VALUES ($1,$2,$3::outcome_type,$4,$5)
        """, uuid.uuid4(), sess_id, outcome,
             f"Call ended with outcome: {outcome}", ended)

        # ── follow_up ─────────────────────────────────────────────────────
        if outcome in ("interested", "future_follow_up", "pending"):
            await conn.execute("""
                INSERT INTO follow_ups
                  (id, customer_id, call_session_id, agent_type_id,
                   scheduled_at, reason, status, created_at)
                VALUES ($1,$2,$3,$4,$5,$6,'pending'::follow_up_status,$7)
            """, uuid.uuid4(), cid, sess_id, agent_id,
                 ended + timedelta(days=random.randint(1, 14)),
                 "Customer showed interest — schedule follow-up", ended)

        # ── subscription link ─────────────────────────────────────────────
        if outcome in ("payment_made", "interested", "renewed") and cid in sub_map:
            pay_status = "paid" if outcome == "payment_made" else "opened"
            opened_at = ended + timedelta(minutes=5)
            paid_at = ended + timedelta(minutes=10) if outcome == "payment_made" else None
            await conn.execute("""
                INSERT INTO subscription_links
                  (id, subscription_id, call_session_id, link_url,
                   payment_status, sent_at, opened_at, payment_made_at, created_at)
                VALUES ($1,$2,$3,$4,$5::payment_status,$6,$7,$8,$6)
            """, uuid.uuid4(), sub_map[cid], sess_id,
                 f"https://pay.example/{uuid.uuid4().hex[:12]}",
                 pay_status, ended, opened_at, paid_at)

        # ── MCP tool calls ────────────────────────────────────────────────
        for tool in random.sample(MCP_TOOLS, k=random.randint(2, 5)):
            success = random.random() > 0.05
            await conn.execute("""
                INSERT INTO mcp_tool_calls
                  (id, call_session_id, tool_name, input_json, output_json,
                   duration_ms, success, called_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
            """, uuid.uuid4(), sess_id, tool,
                 f'{{"customer_id":"{cid}"}}',
                 '{"status":"ok"}' if success else None,
                 random.randint(10, 200), success,
                 started + timedelta(seconds=random.randint(5, dur - 5)))

    print(f"  {session_count} call sessions")

    print("\nFinal row counts:")
    for t in ["customers", "call_sessions", "conversation_transcripts",
              "call_outcomes", "follow_ups", "mcp_tool_calls",
              "subscription_links", "subscriptions"]:
        n = await conn.fetchval(f"SELECT COUNT(*) FROM {t}")
        print(f"  {t:32} {n}")

    await conn.close()
    print("\nSeed complete!")

asyncio.run(seed())
