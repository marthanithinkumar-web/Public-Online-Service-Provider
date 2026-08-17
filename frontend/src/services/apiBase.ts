export const apiBase = (() => {
  const base = import.meta.env.VITE_API_URL || ''
  const trimmed = String(base).replace(/\/+$/, '')
  return trimmed ? `${trimmed}/api` : '/api'
})()
