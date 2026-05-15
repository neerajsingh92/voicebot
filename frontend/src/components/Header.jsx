export default function Header({ pref, setTheme, range, setRange }) {
  const opts = [
    { id: 'dark',  icon: 'moon', label: 'Dark'  },
    { id: 'light', icon: 'sun',  label: 'Light' },
  ]

  return (
    <div className="app-header">
      <div className="brand-block">
        <div className="brand-mark" aria-hidden="true">
          <i className="ti ti-headset" />
        </div>
        <div>
          <div className="hdr-title">
            Voicebot Command Center
          </div>
          <div className="hdr-sub">Live calls, payments, follow-ups and system health</div>
        </div>
      </div>

      <div className="hdr-right">
        <div className="badge-live">
          <span className="dot-live" aria-hidden="true" />
          Live
        </div>

        <div className="t-pill" role="group" aria-label="Colour theme">
          {opts.map(o => (
            <button
              key={o.id}
              className={`t-opt${pref === o.id ? ' active' : ''}`}
              onClick={() => setTheme(o.id)}
              aria-label={o.label}
              aria-pressed={pref === o.id}
            >
              <i className={`ti ti-${o.icon}`} aria-hidden="true" />
              {o.label}
            </button>
          ))}
        </div>

        <div className="hdr-sep" aria-hidden="true" />

        <div className="range-tabs" role="group" aria-label="Date range">
          {['1d','7d','30d'].map(r => (
            <button
              key={r}
              className={`tbtn${range === r ? ' active' : ''}`}
              onClick={() => setRange(r)}
            >
              {r === '1d' ? 'Today' : r === '7d' ? '7 days' : '30 days'}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
