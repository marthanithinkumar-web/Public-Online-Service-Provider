import axios from 'axios'
import { saveToken, getToken, clearToken } from './localStorage'

const api = axios.create({ baseURL: '/api' })

export async function register(email:string, password:string){
  const res = await api.post('/auth/register', { email, password })
  if(res.data?.token){
    saveToken(res.data.token)
  }
  return res.data
}

export async function login(email:string, password:string){
  const res = await api.post('/auth/login', { email, password })
  if(res.data?.token){
    saveToken(res.data.token)
  }
  return res.data
}

export function logout(){
  clearToken()
}

export function authHeader(){
  const t = getToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}
