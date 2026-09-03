import axios from 'axios'
import {apiBase} from './apiBase'

export type JobSource={key:string;name:string;listing_url:string;last_sync_completed_at?:string|null;last_sync_status?:string;fetched_count?:number;published_count?:number;last_error?:string|null;enabled?:boolean}
export type JobFeeFactor={key:string;label:string;type:'select'|'text'|'boolean';options?:string[];required?:boolean}
export type JobFeeRule={amount_inr:number;conditions:Record<string,string[]>;label?:string;priority?:number}
export type JobNotification={
  id:number;slug:string;title:string;organization:string;job_type:'government'|'private';appointment_type?:string|null;
  location?:string|null;qualification?:string|null;age_limit?:string|null;application_fee?:string|null;fee_factors?:JobFeeFactor[];fee_rules_verified?:boolean;fee_rules?:JobFeeRule[];fee_rules_verified_at?:string|null;vacancies?:string|null;
  salary?:string|null;summary?:string|null;issue_date?:string|null;application_start_date?:string|null;deadline?:string|null;
  official_notice_url:string;application_url?:string|null;status:string;verification_status:string;is_featured:boolean;
  source?:JobSource|null;first_seen_at?:string|null;last_seen_at?:string|null;published_at?:string|null;confidence?:number;
  content_hash?:string;
}

export type JobFeedData={items:JobNotification[];count:number;sources?:JobSource[];generated_at?:string|null;successful_sources?:number;review_count?:number}

const api=axios.create({baseURL:apiBase,timeout:8000})
let snapshotCache:JobFeedData|null=null
let snapshotPromise:Promise<JobFeedData>|null=null

async function fetchSnapshot(force=false){
  if(snapshotCache&&!force)return snapshotCache
  if(snapshotPromise&&!force)return snapshotPromise
  snapshotPromise=(async()=>{
    const response=await fetch('/data/jobs.json',{cache:'default',headers:{Accept:'application/json'}})
    if(!response.ok)throw new Error('Verified job snapshot is unavailable.')
    const data=await response.json() as JobFeedData
    snapshotCache=data
    return data
  })()
  try{return await snapshotPromise}finally{snapshotPromise=null}
}

function filterSnapshot(data:JobFeedData,params:Record<string,string|number|boolean>){
  const term=String(params.q||'').trim().toLowerCase()
  const aliases:Record<string,string>={govt:'government',railways:'railway'}
  const tokens=Array.from(new Set(term.replace(/[^a-z0-9]+/g,' ').split(' ').filter(Boolean).map(token=>aliases[token]||token)))
  const type=String(params.type||'').trim().toLowerCase()
  const featured=['1','true','yes'].includes(String(params.featured||'').toLowerCase())
  const requested=Number(params.limit||30)
  const limit=Number.isFinite(requested)?Math.min(100,Math.max(1,requested)):30
  const items=(data.items||[]).filter(job=>{
    if(type&&job.job_type!==type)return false
    if(featured&&!job.is_featured)return false
    if(!tokens.length)return true
    const searchable=[job.title,job.organization,job.qualification,job.location,job.source?.name,job.source?.key]
      .map(value=>String(value||'').toLowerCase()).join(' ')
    return tokens.every(token=>searchable.includes(token))
  }).slice(0,limit)
  return {...data,items,count:items.length}
}

async function refreshJobsInBackground(params:Record<string,string|number|boolean>){
  try{
    const fresh=(await api.get('/jobs/',{params,timeout:3500})).data as JobFeedData
    if(!Object.keys(params).length||(!params.q&&!params.type&&!params.featured))snapshotCache=fresh
  }catch{
    // The checked-in verified snapshot remains the last-known-good result.
  }
}

export async function fetchJobs(params:Record<string,string|number|boolean>={}){
  try{
    const snapshot=filterSnapshot(await fetchSnapshot(),params)
    void refreshJobsInBackground(params)
    return snapshot
  }catch{
    return (await api.get('/jobs/',{params})).data as JobFeedData
  }
}

export async function fetchJob(slug:string){
  try{
    const data=await fetchSnapshot()
    const job=(data.items||[]).find(item=>item.slug===slug)
    if(job){void api.get(`/jobs/${encodeURIComponent(slug)}`,{timeout:3500}).catch(()=>undefined);return {job}}
  }catch{
    // Fall through to the live API when the snapshot cannot be loaded.
  }
  return (await api.get(`/jobs/${encodeURIComponent(slug)}`)).data as {job:JobNotification}
}

export async function fetchJobSources(){
  try{
    const data=await fetchSnapshot()
    return {items:data.sources||[]}
  }catch{
    return (await api.get('/jobs/sources')).data as {items:JobSource[]}
  }
}

export const jobPath=(job:Pick<JobNotification,'slug'>)=>`/jobs/${job.slug}`

export function formatJobDate(value?:string|null){
  if(!value)return 'See official notice'
  const parsed=new Date(`${value}T00:00:00`)
  return Number.isNaN(parsed.getTime())?value:parsed.toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})
}

export function deadlineText(value?:string|null){
  if(!value)return 'Date in official notice'
  const end=new Date(`${value}T23:59:59`)
  const days=Math.ceil((end.getTime()-Date.now())/86400000)
  if(days<0)return 'Closed'
  if(days===0)return 'Last day today'
  return `${days} day${days===1?'':'s'} left`
}
