import axios from 'axios'
import {apiBase} from './apiBase'

const CACHE_KEY='psp_service_catalog_v1'
const MAX_AGE_MS=15*60*1000
const STALE_MAX_AGE_MS=7*24*60*60*1000
const REQUEST_TIMEOUT_MS=12000
let request:Promise<any[]>|null=null

export function readCachedServices(allowStale=false):any[]{
  try{
    const cached=JSON.parse(localStorage.getItem(CACHE_KEY)||'null')
    const maxAge=allowStale?STALE_MAX_AGE_MS:MAX_AGE_MS
    if(!cached||Date.now()-cached.saved_at>=maxAge||!Array.isArray(cached.items))return[]
    return cached.items.filter((item:any)=>item&&Number.isFinite(Number(item.id))&&typeof item.name==='string')
  }catch{return[]}
}

export async function fetchServiceCatalog(force=false):Promise<any[]>{
  const cached=readCachedServices()
  if(cached.length&&!force)return cached
  if(request)return request
  request=axios.get(`${apiBase}/services`,{timeout:REQUEST_TIMEOUT_MS}).then(response=>{const items=Array.isArray(response.data)?response.data:[];try{localStorage.setItem(CACHE_KEY,JSON.stringify({saved_at:Date.now(),items}))}catch{}return items}).finally(()=>{request=null})
  return request
}

export function clearServiceCatalog(){try{localStorage.removeItem(CACHE_KEY)}catch{}}
