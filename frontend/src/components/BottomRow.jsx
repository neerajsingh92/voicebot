import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

const PILL = { done:'pill-done', pend:'pill-pend', work:'pill-work', fail:'pill-fail' }
const CLRK = { teal:'var(--teal-c)', blue:'var(--blue-c)', purple:'var(--purp-c)', amber:'var(--ambr-c)', red:'var(--red-c)', gray:'var(--gray-c)' }

/* ── Sessions table ──────────────────────────────────────── */
function SessionsTable({ data, loading }) {
  if (loading || !data) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-list-details" aria-hidden="true" />Recent sessions</div>
      {[...Array(5)].map((_,i) => <div key={i} className="skeleton" style={{ height:32, marginBottom:4, borderRadius:4 }} />)}
    </div>
  )
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-list-details" aria-hidden="true" />
            Recent sessions
          </div>
          <p className="card-subtitle">Latest customer conversations and outcomes</p>
        </div>
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>Customer</th><th>Agent</th><th>Outcome</th><th>Dur.</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          {data.map(s => (
            <tr key={s.id}>
              <td>
                <div style={{ display:'flex', alignItems:'center', gap:7 }}>
                  <div className="avatar" style={{ background:`var(--${s.color_key}-bg)`, color:CLRK[s.color_key] }}>
                    {s.initials}
                  </div>
                  {s.customer_name}
                </div>
              </td>
              <td><span style={{ fontSize:10, color:CLRK[s.color_key] }}>{s.agent}</span></td>
              <td><span className={`pill ${PILL[s.status_key]}`}>{s.outcome}</span></td>
              <td style={{ fontVariantNumeric:'tabular-nums' }}>{s.duration}</td>
              <td><span className={`pill ${PILL[s.status_key]}`}>{s.status}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ marginTop:10, textAlign:'right' }}>
        <button className="outline-action">
          Export CSV
        </button>
      </div>
    </div>
  )
}

/* ── MCP tool bars ───────────────────────────────────────── */
function McpCard({ data, loading }) {
  if (loading || !data) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-cpu" aria-hidden="true" />MCP tool calls</div>
      {[...Array(7)].map((_,i) => <div key={i} className="skeleton" style={{ height:16, marginBottom:6, borderRadius:3 }} />)}
    </div>
  )
  const max = data.tools[0]?.count || 1
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-cpu" aria-hidden="true" />
            MCP tool calls
          </div>
          <p className="card-subtitle">Automation usage and reliability</p>
        </div>
      </div>
      <div style={{ display:'flex', alignItems:'baseline', gap:6, marginBottom:12 }}>
        <span style={{ fontSize:20, fontWeight:700, color:'var(--text)' }}>{data.total.toLocaleString()}</span>
        <span style={{ fontSize:11, color:'var(--text3)' }}>{data.success_rate}% success</span>
      </div>
      {data.tools.map(t => (
        <div className="mcp-row" key={t.name}>
          <span className="mcp-name">{t.name}</span>
          <div className="mcp-track">
            <div className="mcp-fill" style={{ width:`${Math.round(t.count/max*100)}%`, background:t.color }} />
          </div>
          <span className="mcp-cnt">{t.count.toLocaleString()}</span>
        </div>
      ))}
      <div style={{ marginTop:10, paddingTop:8, borderTop:'1px solid var(--border)', display:'flex', justifyContent:'space-between', fontSize:11, color:'var(--text3)' }}>
        <span>Avg: <strong style={{ color:'var(--text)' }}>{data.avg_ms}ms</strong></span>
        <span>Failures: <strong style={{ color:'var(--red-c)' }}>{data.failures}</strong></span>
      </div>
    </div>
  )
}

/* ── System health + sub status chart ────────────────────── */
function themeVals() {
  const dk = document.documentElement.dataset.theme === 'dark'
  return {
    grid:   dk ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
    tick:   dk ? '#475569' : '#94A3B8',
    tipBg:  dk ? '#1A2236' : '#1E293B',
    tipBdr: dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.15)',
  }
}

function HealthCard({ healthData, subData, loading, theme }) {
  const ref = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!subData || !ref.current) return
    chartRef.current?.destroy()
    const t = themeVals()
    chartRef.current = new Chart(ref.current, {
      type: 'bar',
      data: {
        labels: subData.labels,
        datasets: [{ data: subData.data, backgroundColor: subData.colors, borderRadius: 8, borderSkipped: false }],
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: t.tipBg, borderColor: t.tipBdr, borderWidth: 1, titleColor: '#94A3B8', bodyColor: '#E2E8F0', padding: 8, cornerRadius: 6 },
        },
        scales: {
          x: { grid: { color: t.grid }, ticks: { color: t.tick, font: { size: 10 } } },
          y: { grid: { display: false }, ticks: { color: t.tick, font: { size: 10 } } },
        },
      },
    })
    return () => { chartRef.current?.destroy(); chartRef.current = null }
  }, [subData, theme])

  if (loading || !healthData) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-heartbeat" aria-hidden="true" />System health</div>
      {[...Array(5)].map((_,i) => <div key={i} className="skeleton" style={{ height:28, marginBottom:4, borderRadius:4 }} />)}
    </div>
  )

  const iconMap = { phone:'phone', brain:'brain', cpu:'cpu', database:'database', server:'server' }
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-heartbeat" aria-hidden="true" />
            System health
          </div>
          <p className="card-subtitle">Connected services and subscription mix</p>
        </div>
      </div>
      {healthData.services.map(s => (
        <div className="health-row" key={s.name}>
          <div className="h-name">
            <i className={`ti ti-${iconMap[s.icon] || 'circle'}`} aria-hidden="true" />
            {s.name}
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span className="h-lat">{s.latency}</span>
            <span className={`pill ${PILL[s.status_key]}`}>{s.status}</span>
          </div>
        </div>
      ))}
      <div style={{ marginTop:14, paddingTop:12, borderTop:'1px solid var(--border)' }}>
        <div className="card-title" style={{ marginBottom:8 }}>
          <i className="ti ti-chart-bar" aria-hidden="true" />
          Subscription status
        </div>
        <div className="chart-wrap" style={{ height:80 }}>
          {subData
            ? <canvas ref={ref} role="img" aria-label="Horizontal bar showing subscription status split." />
            : <div className="skeleton" style={{ height:'100%', borderRadius:6 }} />
          }
        </div>
      </div>
    </div>
  )
}

/* ── Composed bottom row ─────────────────────────────────── */
export default function BottomRow({ sessions, mcpTools, health, subStatus, loading, theme }) {
  return (
    <div className="g31">
      <SessionsTable data={sessions} loading={loading} />
      <McpCard       data={mcpTools} loading={loading} />
      <HealthCard    healthData={health} subData={subStatus} loading={loading} theme={theme} />
    </div>
  )
}
