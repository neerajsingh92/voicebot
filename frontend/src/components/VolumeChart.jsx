import { useEffect, useRef } from 'react'
import Chart from 'chart.js/auto'

function barColors(data) {
  return data.map(v => v >= 30 ? '#059669' : v >= 20 ? '#2563EB' : v >= 10 ? '#7C3AED' : '#94A3B8')
}

function themeVals() {
  const dk = document.documentElement.dataset.theme === 'dark'
  return {
    grid:   dk ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)',
    tick:   dk ? '#475569' : '#94A3B8',
    tipBg:  dk ? '#1A2236' : '#1E293B',
    tipBdr: dk ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.15)',
  }
}

export default function VolumeChart({ data, loading, theme }) {
  const ref = useRef(null)
  const chartRef = useRef(null)

  useEffect(() => {
    if (!data || !ref.current) return
    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null }

    const t = themeVals()
    chartRef.current = new Chart(ref.current, {
      type: 'bar',
      data: {
        labels: data.labels,
        datasets: [{
          label: 'Calls',
          data: data.data,
          backgroundColor: barColors(data.data),
          borderRadius: 8,
          borderSkipped: false,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: t.tipBg, borderColor: t.tipBdr, borderWidth: 1,
            titleColor: '#94A3B8', bodyColor: '#E2E8F0', padding: 10, cornerRadius: 8,
          },
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: t.tick, maxRotation: 0, autoSkip: true, font: { size: 11, family: "'DM Sans', system-ui" } } },
          y: { grid: { color: t.grid },  ticks: { color: t.tick, stepSize: 10,   font: { size: 11, family: "'DM Sans', system-ui" } } },
        },
      },
    })
    return () => { chartRef.current?.destroy(); chartRef.current = null }
  }, [data, theme])

  return (
    <div className="card chart-card">
      <div className="card-head">
        <div>
          <div className="card-title">
            <i className="ti ti-chart-bar" aria-hidden="true" />
            Call volume
          </div>
          <p className="card-subtitle">Inbound and outbound sessions over the selected range</p>
        </div>
      </div>
      <div className="chart-wrap" style={{ height: 220 }}>
        {loading
          ? <div className="skeleton" style={{ height: '100%', borderRadius: 6 }} />
          : data?.no_data
            ? <div className="no-data-center"><i className="ti ti-chart-bar-off" /><span>No call volume data for this period</span></div>
            : <canvas ref={ref} role="img" aria-label="Bar chart of call volume by time period." />
        }
      </div>
    </div>
  )
}
