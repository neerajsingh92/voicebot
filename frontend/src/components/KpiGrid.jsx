function KpiCard({ icon, label, value, sub, delta, deltaType = 'up', accent }) {
  return (
    <div className="kpi" style={{ '--kpi-ac': accent }}>
      <div className="kpi-top">
        <div className="kpi-icon" aria-hidden="true">
          <i className={`ti ti-${icon}`} />
        </div>
        {delta && <span className={`kpi-delta delta-${deltaType}`}>{delta}</span>}
      </div>
      <div className="kpi-label">{label}</div>
      <div className="kpi-value">{value ?? '—'}</div>
      <div className="kpi-sub">{sub}</div>
    </div>
  )
}

function Skeleton() {
  return (
    <div className="kpi">
      <div className="skeleton" style={{ height: 11, width: '50%', marginBottom: 10 }} />
      <div className="skeleton" style={{ height: 28, width: '60%', marginBottom: 8 }} />
      <div className="skeleton" style={{ height: 11, width: '70%' }} />
    </div>
  )
}

export default function KpiGrid({ data, loading }) {
  if (loading || !data) {
    return (
      <>
        <div className="g4">{[...Array(4)].map((_,i) => <Skeleton key={i} />)}</div>
        <div className="g4" style={{ marginBottom: 20 }}>{[...Array(4)].map((_,i) => <Skeleton key={i} />)}</div>
      </>
    )
  }

  const fmt = n => typeof n === 'number' ? n.toLocaleString() : n

  return (
    <>
      <div className="g4">
        <KpiCard icon="phone-call" label="Total calls"    accent="#2563EB" value={fmt(data.total_calls)}        delta="+18"            sub="Compared with yesterday"  />
        <KpiCard icon="circle-check" label="Completed"    accent="#059669" value={fmt(data.completed_calls)}    delta={`${data.completion_rate}%`} sub="Completion rate" />
        <KpiCard icon="credit-card" label="Payments"      accent="#D97706" value={fmt(data.payments_received)}  delta="₹1.14L"          sub="Collected today"         />
        <KpiCard icon="calendar-due" label="Follow-ups"   accent="#7C3AED" value={fmt(data.pending_follow_ups)} delta="+6"    deltaType="dn" sub="New follow-ups today"  />
      </div>
      <div className="g4" style={{ marginBottom: 20 }}>
        <KpiCard icon="activity" label="Active subscriptions" accent="#059669" value={fmt(data.active_subscriptions)} delta="+21"          sub="Added this week"     />
        <KpiCard icon="clock"    label="Average duration"     accent="#2563EB" value={data.avg_duration_str}           sub="Minutes per conversation" />
        <KpiCard icon="cpu"      label="MCP tool calls"       accent="#7C3AED" value={fmt(data.mcp_calls)}             delta={`${data.mcp_success_rate}%`} sub="Success rate" />
        <KpiCard icon="file-text" label="Transcripts saved"   accent="#D97706" value={fmt(data.transcripts_saved)}     sub="Conversation turns logged"  />
      </div>
    </>
  )
}
