import axios from 'axios'
import { saveToken, saveUser, getToken, clearToken } from './localStorage'
import { apiBase } from './apiBase'

const api = axios.create({ baseURL: apiBase, timeout: 20000 })

export async function register(name:string, phone:string, email:string, password:string){
  const res = await api.post('/auth/register', { name, phone, email, password })
  if(res.data?.token){
    saveToken(res.data.token)
    if(res.data.user)saveUser(res.data.user)
  }
  return res.data
}

export async function login(email:string, password:string){
  const res = await api.post('/auth/login', { email, password })
  if(res.data?.token){
    saveToken(res.data.token)
    if(res.data.user)saveUser(res.data.user)
  }
  return res.data
}

export async function verifyAdmin2FA(challenge_token:string, code:string){
  const res = await api.post('/auth/verify-admin-2fa', {challenge_token, code})
  if(res.data?.token) saveToken(res.data.token)
  if(res.data?.user) saveUser(res.data.user)
  return res.data
}

export async function fetchClientProfile(){
  return (await api.get('/auth/profile', {headers:authHeader()})).data
}

export async function updateClientProfile(payload:any){
  const result=(await api.put('/auth/profile',payload,{headers:authHeader()})).data
  if(result.verification_required)clearToken()
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
