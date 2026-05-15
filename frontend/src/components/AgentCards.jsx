const COLOR_MAP = {
  teal:   { bg: 'var(--teal-bg)', c: 'var(--teal-c)' },
  blue:   { bg: 'var(--blue-bg)', c: 'var(--blue-c)' },
  purple: { bg: 'var(--purp-bg)', c: 'var(--purp-c)' },
  amber:  { bg: 'var(--ambr-bg)', c: 'var(--ambr-c)' },
  red:    { bg: 'var(--red-bg)',  c: 'var(--red-c)'  },
  gray:   { bg: 'var(--gray-bg)', c: 'var(--gray-c)' },
}

function AgentCard({ agent }) {
  const clr = COLOR_MAP[agent.color_key] || COLOR_MAP.teal
  const primaryOutcome = agent.outcomes[0]
  return (
    <div className="agent-card" style={{ '--ag-clr': agent.color }}>
      <div className="agent-hdr">
        <div>
          <div className="agent-name">{agent.name}</div>
          <div className="agent-sub">{agent.subtitle}</div>
        </div>
        <div className="agent-badge" style={{ background: clr.bg, color: clr.c }}>
          {agent.total_calls.toLocaleString()}
        </div>
      </div>

      {agent.total_calls === 0
        ? <div className="no-data-center" style={{ padding: '12px 0' }}><i className="ti ti-phone-off" /><span>No calls this period</span></div>
        : (
          <>
            {primaryOutcome && (
              <div className="agent-hero">
                <span>{primaryOutcome.label}</span>
                <strong>{primaryOutcome.pct}%</strong>
              </div>
            )}
            {agent.outcomes.map(o => (
              <div className="bar-row" key={o.label}>
                <span className="bar-lbl">{o.label}</span>
                <div className="bar-track">
                  <div className="bar-fill" style={{ width: `${o.pct}%`, background: o.color }} />
                </div>
                <span className="bar-pct">{o.pct}%</span>
              </div>
            ))}
          </>
        )
      }

      <div className="agent-stats">
        {agent.stats.map(s => {
          const sc = COLOR_MAP[s.color_key] || COLOR_MAP.gray
          return (
            <div className="ag-stat" key={s.label}>
              <div className="ag-stat-val" style={{ color: sc.c }}>
                {s.value.toLocaleString()}
              </div>
              <div className="ag-stat-lbl">{s.label}</div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AgentSkeleton() {
  return (
    <div className="agent-card" style={{ '--ag-clr': '#888780' }}>
      {[...Array(5)].map((_,i) => (
        <div key={i} className="skeleton" style={{ height: i === 0 ? 32 : 14, marginBottom: 10, borderRadius: 6 }} />
      ))}
    </div>
  )
}

export default function AgentCards({ data, loading }) {
  if (loading || !data) {
    return <div className="g4" style={{ marginBottom: 16 }}>{[...Array(4)].map((_,i) => <AgentSkeleton key={i} />)}</div>
  }
  return (
    <div className="g4" style={{ marginBottom: 16 }}>
      {data.map(agent => <AgentCard key={agent.id} agent={agent} />)}
    </div>
  )
}
