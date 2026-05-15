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
      {data.no_data && (
        <div className="no-data-banner">
          <i className="ti ti-info-circle" /> No call data found for this period
        </div>
      )}
      <div className="g4">
        <KpiCard icon="phone-call"   label="Total calls"          accent="#2563EB" value={fmt(data.total_calls)}          sub="Sessions in selected range"    />
        <KpiCard icon="circle-check" label="Completed"            accent="#059669" value={fmt(data.completed_calls)}      sub={`${data.completion_rate}% completion rate`} />
        <KpiCard icon="credit-card"  label="Payments"             accent="#D97706" value={fmt(data.payments_received)}    sub="Payment outcomes"              />
        <KpiCard icon="calendar-due" label="Follow-ups"           accent="#7C3AED" value={fmt(data.pending_follow_ups)}   sub="Pending actions"               />
      </div>
      <div className="g4" style={{ marginBottom: 20 }}>
        <KpiCard icon="activity"   label="Active subscriptions"   accent="#059669" value={fmt(data.active_subscriptions)} sub="Currently active"              />
        <KpiCard icon="clock"      label="Average duration"       accent="#2563EB" value={data.avg_duration_str}          sub="Minutes per conversation"      />
        <KpiCard icon="cpu"        label="MCP tool calls"         accent="#7C3AED" value={fmt(data.mcp_calls)}            sub={`${data.mcp_success_rate}% success rate`} />
        <KpiCard icon="file-text"  label="Transcripts saved"      accent="#D97706" value={fmt(data.transcripts_saved)}    sub="Conversation turns logged"     />
      </div>
    </>
  )
}
