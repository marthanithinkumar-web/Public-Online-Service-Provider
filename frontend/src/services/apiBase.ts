const configured = String(import.meta.env.VITE_API_URL || '').trim().replace(/\/+$/, '')

export const apiBase = (() => {
  if (configured) return `${configured}/api`

  // Local development uses the Vite proxy. The deployed UI must talk to the
  // separate Render API service when VITE_API_URL is not configured.
  if (typeof window !== 'undefined' && /^(localhost|127\.0\.0\.1)$/.test(window.location.hostname)) {
    return '/api'
  }

  return 'https://public-online-service-provider-api.onrender.com/api'
})()
