const TOKEN_KEY = 'psp_token'
const USER_KEY = 'psp_user'

export type StoredUser = {
  id?: number
  name?: string
  email?: string
  phone?: string
  is_admin?: boolean
}

export function saveToken(token: string){
  localStorage.setItem(TOKEN_KEY, token)
}

export function getToken(): string | null{
  return localStorage.getItem(TOKEN_KEY)
}

export function saveUser(user: StoredUser){
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function getUser(): StoredUser | null{
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function clearToken(){
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
