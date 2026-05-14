import { useState, useEffect, useCallback } from 'react'

export function useApi(fetchFn, deps = []) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await fetchFn()
      setData(result)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load() }, [load])

  return { data, loading, error, reload: load }
}

export function useTheme() {
  const stored = () => {
    try { return localStorage.getItem('vb-theme') || 'dark' } catch { return 'dark' }
  }
  const [pref, setPref] = useState(stored)

  const resolvedTheme = pref === 'system'
    ? (matchMedia('(prefers-color-scheme:dark)').matches ? 'dark' : 'light')
    : pref

  useEffect(() => {
    document.documentElement.dataset.theme = resolvedTheme
  }, [resolvedTheme])

  useEffect(() => {
    const mq = matchMedia('(prefers-color-scheme:dark)')
    const handler = () => {
      if (pref === 'system') {
        document.documentElement.dataset.theme =
          mq.matches ? 'dark' : 'light'
      }
    }
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [pref])

  const setTheme = (p) => {
    setPref(p)
    try { localStorage.setItem('vb-theme', p) } catch {}
  }

  return { pref, resolvedTheme, setTheme }
}
