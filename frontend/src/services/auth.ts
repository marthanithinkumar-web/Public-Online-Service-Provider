import axios from 'axios'
import { saveToken, saveUser, getToken, clearToken } from './localStorage'
import { apiBase } from './apiBase'

const AUTH_TIMEOUT_MS = 60000
const WARM_TIMEOUT_MS = 60000
const api = axios.create({ baseURL: apiBase, timeout: AUTH_TIMEOUT_MS })
const apiOrigin = apiBase.replace(/\/api\/?$/, '')
let warmPromise: Promise<boolean> | null = null

export function warmAuthServer(force=false): Promise<boolean>{
  if(warmPromise && !force)return warmPromise
  warmPromise = axios.get(`${apiOrigin}/health`, { timeout: WARM_TIMEOUT_MS })
    .then(()=>true)
    .catch(()=>false)
    .finally(()=>{ window.setTimeout(()=>{ warmPromise=null }, 15000) })
  return warmPromise
}

function persistSession(data:any){
  if(data?.token){
    saveToken(data.token)
    if(data.user)saveUser(data.user)
  }
  return data
}

export async function register(name:string, phone:string, email:string, password:string){
  const res = await api.post('/auth/register', { name, phone, email, password })
  return persistSession(res.data)
}

export async function login(email:string, password:string){
  try{
    const res = await api.post('/auth/login', { email, password })
    return persistSession(res.data)
  }catch(err:any){
    const transient = err?.code==='ECONNABORTED' || err?.code==='ERR_NETWORK' || !err?.response
    if(!transient)throw err
    await warmAuthServer(true)
    const retry = await api.post('/auth/login', { email, password }, { timeout: AUTH_TIMEOUT_MS })
    return persistSession(retry.data)
  }
}

export async function fetchClientProfile(){
  return (await api.get('/auth/profile', {headers:authHeader()})).data
}

export async function updateClientProfile(payload:any){
  const result=(await api.put('/auth/profile',payload,{headers:authHeader()})).data
  if(result.token)saveToken(result.token)
  if(result.user)saveUser(result.user)
  return result
}

export async function deleteAccount(current_password:string){
  const res = await api.delete('/auth/delete-account', {
    headers: authHeader(),
    data: { current_password }
  })
  clearToken()
  return res.data
}

export function logout(){
  const headers=authHeader()
  if(headers.Authorization)fetch(`${apiBase}/auth/logout`,{method:'POST',headers,keepalive:true}).catch(()=>{})
  clearToken()
}

export function authHeader(): Record<string, string>{
  const t = getToken()
  return t ? { Authorization: 'Bearer ' + t } : {}
}
