import { getToken, clearToken } from './localStorage'

export type SessionUser = {
  user_id?: number
  is_admin?: boolean
  exp?: number
}

function decodePayload(token: string): SessionUser | null {
  try {
    const payload = token.split('.')[1]
    if (!payload) return null
    const normalized = payload.replace(/-/g, '+').replace(/_/g, '/')
    const json = decodeURIComponent(atob(normalized).split('').map(c => `%${('00' + c.charCodeAt(0).toString(16)).slice(-2)}`).join(''))
    return JSON.parse(json)
  } catch {
    return null
  }
}

export function getSession(): SessionUser | null {
  const token = getToken()
  if (!token) return null
  const user = decodePayload(token)
  if (!user) {
    clearToken()
    return null
  }
  if (user.exp && user.exp * 1000 <= Date.now()) {
    clearToken()
    return null
  }
  return user
}

export function isAuthenticated() {
  return !!getSession()
}

export function isAdmin() {
  return !!getSession()?.is_admin
}
