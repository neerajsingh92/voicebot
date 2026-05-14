const BASE = import.meta.env.VITE_API_URL || ''

async function get(path) {
  const res = await fetch(BASE + path)
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`)
  return res.json()
}

export const api = {
  dashboard:   (range) => get(`/api/dashboard?range=${range}`),
  callVolume:  (range) => get(`/api/call-volume?range=${range}`),
  agents:      (range) => get(`/api/agents?range=${range}`),
  outcomes:    (range) => get(`/api/outcomes?range=${range}`),
  funnel:      (range) => get(`/api/funnel?range=${range}`),
  followUps:   ()      => get('/api/follow-ups'),
  sessions:    (limit) => get(`/api/sessions?limit=${limit}`),
  mcpTools:    (range) => get(`/api/mcp-tools?range=${range}`),
  healthStatus:()      => get('/api/health-status'),
  subStatus:   ()      => get('/api/subscriptions/status'),
}
