import axios from 'axios'
import {apiBase} from './apiBase'

export type JobSource={key:string;name:string;listing_url:string;last_sync_completed_at?:string|null;last_successful_sync_at?:string|null;last_sync_status?:string;consecutive_failures?:number;fetched_count?:number;published_count?:number;last_error?:string|null;enabled?:boolean}
export type JobFeeFactor={key:string;label:string;type:'select'|'text'|'boolean';options?:string[];required?:boolean}
export type JobFeeRule={amount_inr:number;conditions:Record<string,string[]>;label?:string;priority?:number}
export type JobNotification={
  id:number;slug:string;title:string;organization:string;job_type:'government'|'private';appointment_type?:string|null;
  location?:string|null;qualification?:string|null;age_limit?:string|null;application_fee?:string|null;fee_factors?:JobFeeFactor[];fee_rules_verified?:boolean;fee_rules?:JobFeeRule[];fee_rules_verified_at?:string|null;vacancies?:string|null;
  salary?:string|null;summary?:string|null;issue_date?:string|null;application_start_date?:string|null;deadline?:string|null;deadline_cutoff_time?:string|null;deadline_timezone?:string|null;application_status?:'open'|'deadline_today'|'closed'|'unverified';can_apply?:boolean;status_label?:string;
  official_notice_url:string;application_url?:string|null;status:string;verification_status:string;is_featured:boolean;
  source?:JobSource|null;first_seen_at?:string|null;last_seen_at?:string|null;published_at?:string|null;confidence?:number;
  content_hash?:string;
}

export type JobFeedData={items:JobNotification[];count:number;total?:number;verified_open_count?:number;deadline_today_count?:number;sources?:JobSource[];generated_at?:string|null;successful_sources?:number;review_count?:number}

const api=axios.create({baseURL:apiBase,timeout:8000})
let snapshotCache:JobFeedData|null=null
let snapshotPromise:Promise<JobFeedData>|null=null

const PRIORITY_JOB_SOURCES=['rrb','ssc','india_post_gds','india_post','upsc','sbi']
function jobPriority(job:JobNotification){
  const key=String(job.source?.key||'').toLowerCase()
  const name=`${job.source?.name||''} ${job.organization||''}`.toLowerCase()
  const direct=PRIORITY_JOB_SOURCES.indexOf(key)
  if(direct>=0)return direct
  if(name.includes('railway recruitment'))return 0
  if(name.includes('staff selection commission'))return 1
  if(name.includes('india post')||name.includes('department of posts'))return 2
  if(name.includes('union public service commission')||name.includes('upsc'))return 3
  if(name.includes('state bank of india')||name.includes('sbi'))return 4
  return 100
}
function compareJobs(a:JobNotification,b:JobNotification){
  const priority=jobPriority(a)-jobPriority(b)
  if(priority)return priority
  const aDate=Date.parse(a.deadline||a.issue_date||a.published_at||'')||0
  const bDate=Date.parse(b.deadline||b.issue_date||b.published_at||'')||0
  return bDate-aDate
}

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

function zonedParts(timeZone='Asia/Kolkata'){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date())
  const value=Object.fromEntries(parts.map(part=>[part.type,part.value]))
  return {date:`${value.year}-${value.month}-${value.day}`,time:`${value.hour}:${value.minute}:${value.second}`}
}
function indiaToday(){return zonedParts('Asia/Kolkata').date}
function sourceIsFresh(job:JobNotification){
  const source=job.source
  if(!source||!['success','running'].includes(String(source.last_sync_status||'')))return false
  const checked=Date.parse(source.last_successful_sync_at||source.last_sync_completed_at||'')
  const seen=Date.parse(job.last_seen_at||'')
  const age=Date.now()-checked
  const seenAge=Date.now()-seen
  return Number.isFinite(checked)&&Number.isFinite(seen)&&age>=-5*60*1000&&age<=36*60*60*1000&&seenAge>=-5*60*1000&&seenAge<=36*60*60*1000
}
function deadlineState(job:JobNotification){
  const deadline=String(job.deadline||'')
  if(!/^\d{4}-\d{2}-\d{2}$/.test(deadline))return 'unverified'
  const timeZone=job.deadline_timezone||'Asia/Kolkata'
  let local
  try{local=zonedParts(timeZone)}catch{return 'unverified'}
  if(deadline<local.date)return 'closed'
  if(deadline>local.date)return 'open'
  const cutoff=String(job.deadline_cutoff_time||'').slice(0,5)
  if(cutoff&&local.time.slice(0,5)>=cutoff)return 'closed'
  return 'deadline_today'
}
export function jobApplicationStatus(job:JobNotification){
  if(job.status!=='published'||!sourceIsFresh(job))return 'unverified'
  return deadlineState(job)
}
export function jobStatusLabel(job:JobNotification){
  const state=jobApplicationStatus(job)
  if(state==='closed')return 'Closed—deadline passed'
  if(state==='deadline_today'){
    const cutoff=String(job.deadline_cutoff_time||'').slice(0,5)
    return cutoff? `Deadline today—closes at ${cutoff} IST` : 'Deadline today—check official portal'
  }
  if(state==='open')return 'Verified open'
  return 'Unverified—check official source'
}
export function jobCanApply(job:JobNotification){
  const state=jobApplicationStatus(job)
  if(state==='open')return true
  return state==='deadline_today'&&Boolean(job.deadline_cutoff_time)
}
export function jobLastVerified(job:JobNotification){
  const value=job.source?.last_successful_sync_at||job.source?.last_sync_completed_at||job.last_seen_at
  if(!value)return 'Last verified date unavailable'
  const parsed=new Date(value)
  return Number.isNaN(parsed.getTime())?'Last verified date unavailable':`Last verified ${parsed.toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata',day:'numeric',month:'short',year:'numeric'})}`
}
function hasCurrentDeadline(value?:string|null){
  if(!value||!/^\d{4}-\d{2}-\d{2}$/.test(value))return false
  const parsed=new Date(value+'T00:00:00Z')
  return !Number.isNaN(parsed.getTime())&&parsed.toISOString().slice(0,10)===value&&value>=indiaToday()
}
function isVerifiedPublicJob(job:JobNotification){
  return job.status==='published'&&sourceIsFresh(job)&&hasCurrentDeadline(job.deadline)&&deadlineState(job)!=='closed'
}

function filterSnapshot(data:JobFeedData,params:Record<string,string|number|boolean>){
  const term=String(params.q||'').trim().toLowerCase()
  const aliases:Record<string,string>={govt:'government',railways:'railway'}
  const tokens=Array.from(new Set(term.replace(/[^a-z0-9]+/g,' ').split(' ').filter(Boolean).map(token=>aliases[token]||token)))
  const requestedType=String(params.type||'').trim().toLowerCase()
  const type=['government','private'].includes(requestedType)?requestedType:''
  const featured=['1','true','yes'].includes(String(params.featured||'').toLowerCase())
  const location=String(params.location||'').trim().toLowerCase()
  const qualification=String(params.qualification||'').trim().toLowerCase()
  const rawLimit=params.limit
  const requested=rawLimit===undefined||rawLimit===null||rawLimit===''?30:Number(rawLimit)
  const limit=Number.isFinite(requested)?Math.min(100,Math.max(1,requested)):30
  const items=(data.items||[]).filter(job=>{
    if(!isVerifiedPublicJob(job))return false
    if(type&&job.job_type!==type)return false
    if(featured&&!job.is_featured)return false
    if(location&&!String(job.location||'').toLowerCase().includes(location))return false
    if(qualification&&!String(job.qualification||'').toLowerCase().includes(qualification))return false
    if(!tokens.length)return true
    const searchable=[job.title,job.organization,job.qualification,job.location,job.source?.name,job.source?.key]
      .map(value=>String(value||'').toLowerCase()).join(' ')
    return tokens.every(token=>searchable.includes(token))
  }).sort(compareJobs).slice(0,limit)
  return {...data,items,count:items.length,total:items.length,verified_open_count:items.filter(job=>jobApplicationStatus(job)==='open').length,deadline_today_count:items.filter(job=>jobApplicationStatus(job)==='deadline_today').length}
}

async function refreshJobsInBackground(params:Record<string,string|number|boolean>){
  try{
    // Ping the live API so its background sync can run, but never replace the
    // checked-in verified snapshot cache with a potentially lagging DB result.
    // Keeping the snapshot stable guarantees that a job just shown in the list
    // can still be resolved when the user opens its detail page.
    await api.get('/jobs/',{params,timeout:3500})
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
    const data=(await api.get('/jobs/',{params})).data as JobFeedData
    const items=(data.items||[]).filter(isVerifiedPublicJob).sort(compareJobs)
    return {...data,items,count:items.length,total:items.length,verified_open_count:items.filter(job=>jobApplicationStatus(job)==='open').length,deadline_today_count:items.filter(job=>jobApplicationStatus(job)==='deadline_today').length}
  }
}

export async function fetchJob(slug:string){
  try{
    const data=await fetchSnapshot()
    const job=(data.items||[]).find(item=>item.slug===slug&&isVerifiedPublicJob(item))
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
  const parsed=new Date(`${value}T00:00:00Z`)
  return Number.isNaN(parsed.getTime())?value:parsed.toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata',day:'numeric',month:'short',year:'numeric'})
}

export function deadlineText(value?:string|null){
  if(!value)return 'Date in official notice'
  const deadline=Date.parse(`${value}T00:00:00Z`)
  const today=Date.parse(`${indiaToday()}T00:00:00Z`)
  if(Number.isNaN(deadline)||Number.isNaN(today))return 'Check official portal'
  const days=Math.round((deadline-today)/86400000)
  if(days<0)return 'Closed — deadline passed'
  if(days===0)return 'Deadline today — check official portal'
  return `${days} day${days===1?'':'s'} left`
}
