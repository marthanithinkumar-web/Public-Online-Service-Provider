import axios from 'axios'
import { saveToken, getToken, clearToken } from './localStorage'
import { apiBase } from './apiBase'

const api = axios.create({ baseURL: apiBase })

export async function register(name:string, phone:string, email:string, password:string){
  const res = await api.post('/auth/register', { name, phone, email, password })
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

export async function deleteAccount(current_password:string){
  const res = await api.delete('/auth/delete-account', {
    headers: authHeader(),
    data: { current_password }
  })
  clearToken()
  return res.data
}

export function logout(){
  clearToken()
}

export function authHeader(){
  const t = getToken()
  return t ? { Authorization: 'Bearer ' + t } : {}
}
