import axios from 'axios'
import {apiBase} from './apiBase'

const CACHE_KEY='psp_service_catalog_v1'
const MAX_AGE_MS=15*60*1000
let request:Promise<any[]>|null=null

export function readCachedServices():any[]{
  try{const cached=JSON.parse(localStorage.getItem(CACHE_KEY)||'null');return cached&&Date.now()-cached.saved_at<MAX_AGE_MS&&Array.isArray(cached.items)?cached.items:[]}catch{return[]}
}

export async function fetchServiceCatalog(force=false):Promise<any[]>{
  const cached=readCachedServices()
  if(cached.length&&!force)return cached
  if(request)return request
  request=axios.get(`${apiBase}/services`,{timeout:20000}).then(response=>{const items=Array.isArray(response.data)?response.data:[];try{localStorage.setItem(CACHE_KEY,JSON.stringify({saved_at:Date.now(),items}))}catch{}return items}).finally(()=>{request=null})
  return request
}

export function clearServiceCatalog(){try{localStorage.removeItem(CACHE_KEY)}catch{}}
