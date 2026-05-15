import { useState } from 'react'
import { useApi, useTheme } from './hooks/useApi'
import { api } from './api'
import Header     from './components/Header'
import KpiGrid    from './components/KpiGrid'
import VolumeChart from './components/VolumeChart'
import AgentCards  from './components/AgentCards'
import MiddleRow   from './components/MiddleRow'
import BottomRow   from './components/BottomRow'

function Section({ eyebrow, title, children }) {
  return (
    <section className="dashboard-section">
      <div className="section-heading">
        <span>{eyebrow}</span>
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  )
}

export default function App() {
  const [range, setRange] = useState('1d')
  const { pref, resolvedTheme, setTheme } = useTheme()

  /* ── All API calls ── */
  const dashboard = useApi(() => api.dashboard(range),   [range])
  const volume    = useApi(() => api.callVolume(range),  [range])
  const agents    = useApi(() => api.agents(range),      [range])
  const outcomes  = useApi(() => api.outcomes(range),    [range])
  const funnel    = useApi(() => api.funnel(range),      [range])
  const followUps = useApi(() => api.followUps(range),        [range])
  const sessions  = useApi(() => api.sessions(range, 6),      [range])
  const mcpTools  = useApi(() => api.mcpTools(range),         [range])
  const health    = useApi(() => api.healthStatus(),           [])
  const subStatus = useApi(() => api.subStatus(range),         [range])

  const anyError = [dashboard, volume, agents, outcomes, funnel].find(d => d.error)
  const rangeTitle = range === '7d' ? 'Last 7 days performance' : range === '30d' ? 'Last 30 days performance' : 'Voicebot performance today'

  return (
    <div className="app-wrap">
      <Header
        pref={pref}
        setTheme={setTheme}
        range={range}
        setRange={setRange}
      />

      {anyError && (
        <div style={{
          background: 'var(--p-fail-bg)', border: '1px solid var(--red-bg)',
          borderRadius: 8, padding: '10px 16px', marginBottom: 16,
          color: 'var(--red-c)', fontSize: 12,
          display: 'flex', alignItems: 'center', gap: 8
        }}>
          <i className="ti ti-alert-triangle" aria-hidden="true" />
          API error: {anyError.error}. Make sure the FastAPI backend is running on port 8000.
          <button
            onClick={() => [dashboard, volume, agents, outcomes, funnel].forEach(d => d.reload())}
            style={{ marginLeft:'auto', background:'transparent', border:'1px solid var(--red-c)', borderRadius:4, color:'var(--red-c)', padding:'2px 8px', cursor:'pointer', fontFamily:'inherit', fontSize:11 }}
          >
            Retry
          </button>
        </div>
      )}

      <Section eyebrow="At a glance" title={rangeTitle}>
        <KpiGrid
          data={dashboard.data}
          loading={dashboard.loading}
        />
      </Section>

      <Section eyebrow="Traffic" title="Call volume trend">
        <VolumeChart
          data={volume.data}
          loading={volume.loading}
          theme={resolvedTheme}
        />
      </Section>

      <Section eyebrow="Agents" title="Conversation teams">
        <AgentCards
          data={agents.data}
          loading={agents.loading}
        />
      </Section>

      <Section eyebrow="Conversion" title="Funnel, outcomes and follow-ups">
        <MiddleRow
          funnel={funnel.data}
          outcomes={outcomes.data}
          followUps={followUps.data}
          loadingFunnel={funnel.loading}
          loadingOutcomes={outcomes.loading}
          loadingQueue={followUps.loading}
          theme={resolvedTheme}
        />
      </Section>

      <Section eyebrow="Operations" title="Recent activity and platform health">
        <BottomRow
          sessions={sessions.data}
          mcpTools={mcpTools.data}
          health={health.data}
          subStatus={subStatus.data}
          loading={sessions.loading || mcpTools.loading || health.loading}
          theme={resolvedTheme}
        />
      </Section>
    </div>
  )
}
