import axios from 'axios'
import {apiBase} from './apiBase'

const CACHE_KEY='psp_service_catalog_v2'
const MAX_AGE_MS=15*60*1000
const STALE_MAX_AGE_MS=7*24*60*60*1000
const REQUEST_TIMEOUT_MS=12000
let request:Promise<any[]>|null=null
let snapshotRequest:Promise<any[]>|null=null
let snapshotItems:any[]|null=null

function normalizeSnapshotService(item:any){
  if(!item||typeof item.name!=='string')return null
  const slug=slugifyServiceName(item.slug||item.name)
  return {...item,slug,__seoSnapshot:true,requirements:item.requirements||{}}
}

function schemaTypeIncludes(value:any,type:string){
  const types=Array.isArray(value)?value:[value]
  return types.some(item=>String(item||'').toLowerCase()===type.toLowerCase())
}

export function readPrerenderedService(slug?:string){
  if(typeof document==='undefined'||typeof window==='undefined'||!slug)return null
  try{
    const raw=document.getElementById('structured-data')?.textContent||''
    const parsed=JSON.parse(raw)
    const entries=Array.isArray(parsed)?parsed:[parsed]
    const normalized=slugifyServiceName(slug)
    const expectedPath=`/services/${normalized}`
    const schema=entries.find(item=>{
      if(!item||!schemaTypeIncludes(item['@type'],'Service'))return false
      const path=new URL(String(item.url||''),window.location.origin).pathname.replace(/\/+$/,'')||'/'
      return path===expectedPath
    })
    if(!schema?.name)return null
    return normalizeSnapshotService({name:String(schema.name),description:String(schema.description||''),category:String(schema.serviceType||'Public Services'),slug:normalized})
  }catch{return null}
}

async function fetchSnapshotCatalog(){
  if(snapshotItems)return snapshotItems
  if(snapshotRequest)return snapshotRequest
  snapshotRequest=fetch('/seo-catalog.json',{cache:'default',headers:{Accept:'application/json'}}).then(async response=>{
    if(!response.ok)throw new Error('Service snapshot is unavailable.')
    const data=await response.json()
    if(!Array.isArray(data))throw new Error('Service snapshot is invalid.')
    snapshotItems=data.map(normalizeSnapshotService).filter(Boolean)
    return snapshotItems
  }).finally(()=>{snapshotRequest=null})
  return snapshotRequest
}

export async function fetchServiceSnapshot(slug:string){
  const normalized=slugifyServiceName(slug)
  return (await fetchSnapshotCatalog()).find(item=>item.slug===normalized)||null
}

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

export function slugifyServiceName(value:string){
  return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'service'
}

export function servicePath(service:any){
  return `/services/${service?.slug||slugifyServiceName(service?.name)}`
}

const ACTION_WORDS=new Set(['apply','application','applications','assistance','service','services'])
export function serviceSearchTokens(value:string){
  return String(value||'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim().replace(/\bgovt\b/g,'government').split(' ').filter(token=>token&&!ACTION_WORDS.has(token))
}

export function isHomepageHighlightEligible(service:any){
  const identity=`${service?.name||''} ${service?.catalog_name||''}`.toLowerCase()
  return !identity.includes('official document pdf access')
}
