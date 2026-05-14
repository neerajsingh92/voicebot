import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

const COLOR_MAP = {
  teal:   'var(--teal-c)', blue:  'var(--blue-c)', purple: 'var(--purp-c)',
  amber:  'var(--ambr-c)', red:   'var(--red-c)',  gray:   'var(--gray-c)',
}

/* ── Funnel ──────────────────────────────────────────────── */
function FunnelCard({ data, loading }) {
  if (loading || !data) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-filter" aria-hidden="true" />Subscription funnel</div>
      {[...Array(5)].map((_,i) => <div key={i} className="skeleton" style={{ height:28, marginBottom:4, borderRadius:4 }} />)}
    </div>
  )
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-filter" aria-hidden="true" />
            Subscription funnel
          </div>
          <p className="card-subtitle">From call started to payment made</p>
        </div>
      </div>
      {data.map(step => (
        <div className="funnel-step" key={step.label}>
          <div className="funnel-lbl">{step.label}</div>
          <div className="funnel-track">
            <div className="funnel-fill" style={{ width: `${step.pct}%`, background: step.color }} />
          </div>
          <div className="funnel-val">{step.value.toLocaleString()}</div>
          <div className="funnel-rate" style={{ color: `var(--${step.color_key}-c)` }}>{step.pct}%</div>
        </div>
      ))}
    </div>
  )
}

/* ── Donut ───────────────────────────────────────────────── */
function themeVals() {
  const dk = document.documentElement.dataset.theme === 'dark'
  return { tipBg: dk?'#1A2236':'#1E293B', tipBdr: dk?'rgba(255,255,255,0.08)':'rgba(0,0,0,0.15)' }
}

function DonutCard({ data, loading, theme }) {
  const ref = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!data || !ref.current) return
    chartRef.current?.destroy()
    const t = themeVals()
    chartRef.current = new Chart(ref.current, {
      type: 'doughnut',
      data: {
        labels: data.map(d => d.label),
        datasets: [{ data: data.map(d => d.value), backgroundColor: data.map(d => d.color), borderWidth: 0, hoverOffset: 4 }],
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '68%',
        plugins: {
          legend: { display: false },
          tooltip: { backgroundColor: t.tipBg, borderColor: t.tipBdr, borderWidth: 1, titleColor: '#94A3B8', bodyColor: '#E2E8F0', padding: 8, cornerRadius: 6 },
        },
      },
    })
    return () => { chartRef.current?.destroy(); chartRef.current = null }
  }, [data, theme])

  if (loading || !data) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-chart-donut" aria-hidden="true" />Outcome breakdown</div>
      <div className="skeleton" style={{ height: 148, width: 148, borderRadius: '50%', margin: '0 auto' }} />
    </div>
  )
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-chart-donut" aria-hidden="true" />
            Outcome breakdown
          </div>
          <p className="card-subtitle">How conversations are ending</p>
        </div>
      </div>
      <div className="donut-wrap">
        <div className="chart-wrap donut-chart" style={{ height: 170, width: 170 }}>
          <canvas ref={ref} role="img" aria-label="Donut chart of call outcome types." />
        </div>
        <div style={{ width:'100%', marginTop:10 }}>
          {data.map(d => (
            <div className="leg-row" key={d.label}>
              <span className="leg-sq" style={{ background: d.color }} />
              {d.label}
              <span className="leg-pct">{d.pct}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── Follow-up queue ─────────────────────────────────────── */
function QueueCard({ data, loading }) {
  if (loading || !data) return (
    <div className="card">
      <div className="card-title"><i className="ti ti-clock-hour-4" aria-hidden="true" />Follow-up queue</div>
      {[...Array(5)].map((_,i) => <div key={i} className="skeleton" style={{ height:28, marginBottom:4, borderRadius:4 }} />)}
    </div>
  )
  return (
    <div className="card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-clock-hour-4" aria-hidden="true" />
            Follow-up queue
          </div>
          <p className="card-subtitle">Open customer actions by agent</p>
        </div>
      </div>
      <div className="queue-total">
        <span style={{ fontSize:22, fontWeight:700, color:'var(--text)' }}>{data.total}</span>
        <span style={{ fontSize:11, color:'var(--text3)' }}>total pending</span>
      </div>
      {data.items.map(item => (
        <div className="queue-row" key={item.reason + item.agent}>
          <div className="q-dot" style={{ background: item.color }} />
          <div className="q-name">{item.agent} · {item.reason}</div>
          <div className="q-cnt" style={{ color: COLOR_MAP[item.color_key] || 'var(--text)' }}>
            {item.count}
          </div>
        </div>
      ))}
      <div style={{ marginTop:12, paddingTop:10, borderTop:'1px solid var(--border)' }}>
        <button
          className="soft-action"
        >
          View all follow-ups
        </button>
      </div>
    </div>
  )
}

/* ── Composed middle row ─────────────────────────────────── */
export default function MiddleRow({ funnel, outcomes, followUps, loadingFunnel, loadingOutcomes, loadingQueue, theme }) {
  return (
    <div className="g3">
      <FunnelCard data={funnel}    loading={loadingFunnel}   />
      <DonutCard  data={outcomes}  loading={loadingOutcomes} theme={theme} />
      <QueueCard  data={followUps} loading={loadingQueue}    />
    </div>
  )
}
