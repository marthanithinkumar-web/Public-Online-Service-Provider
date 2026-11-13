import axios from 'axios'
import {apiBase} from './apiBase'

export type Scholarship={
  id:string;slug:string;title:string;provider:string;source_name:string;source_url:string;application_url:string;
  deadline?:string|null;award?:string|null;region?:string|null;education_level?:string|null;income_limit?:string|null;
  category?:string|null;eligibility?:string|null;documents?:string[];status?:string;verified_at?:string|null;
  source_type?:'official'|'private';is_official?:boolean;source_key?:string;record_type?:'scholarship'|'official_notice';
  academic_year?:string|null;last_seen_at?:string|null;stale_source?:boolean;discovery_method?:string
  application_status?:'open'|'deadline_today'|'closed'|'cancelled'|'unverified';application_scope?:string|null;deadline_type?:string|null;status_evidence?:string|null
  source_checked_at?:string|null;deadline_timezone?:string;deadline_cutoff_time?:string|null;closure_reason?:string|null
}
export type ScholarshipFeed={
  items:Scholarship[];count:number;generated_at?:string|null;official_count?:number;private_count?:number;verified_open_count?:number;deadline_today_count?:number
}

const api=axios.create({baseURL:apiBase,timeout:5000})
const indiaToday=()=>new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())
const rollingOpenEvidence=/\b(?:currently accepting applications|applications? (?:are )?(?:currently )?open|open for applications|registration\b.{0,80}\b(?:is|are)\s+(?:currently\s+)?open|application process is open)\b/i
const sourceCheckIsFresh=(item:Scholarship)=>{
  const checked=Date.parse(item.source_checked_at||item.verified_at||item.last_seen_at||'')
  const age=Date.now()-checked
  return Number.isFinite(checked)&&age>=-5*60*1000&&age<=36*60*60*1000
}
export const scholarshipStatusLabel=(item:Scholarship)=>{
  if(item.application_status==='deadline_today')return 'Deadline today—check official portal'
  if(item.application_status==='open'&&item.application_scope==='renewal_only')return 'Verified open — renewal only'
  if(item.application_status==='open')return 'Verified open'
  if(item.application_status==='closed'||item.status==='closed')return 'Closed—deadline passed'
  return 'Unverified—check official source'
}
export const scholarshipLastVerified=(item:Scholarship)=>{
  const value=item.source_checked_at||item.verified_at||item.last_seen_at
  if(!value)return 'Verification date unavailable'
  const parsed=new Date(value)
  return Number.isNaN(parsed.getTime())?'Verification date unavailable':'Last verified '+parsed.toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric',timeZone:'Asia/Kolkata'})
}
const isActive=(item:Scholarship)=>{
  if(item.status!=='active'||item.stale_source)return false
  if(!(item.is_official===true||item.source_type==='official'))return false
  if(!String(item.status_evidence||'').trim()||!sourceCheckIsFresh(item))return false
  const status=item.application_status
  if(item.deadline&&item.deadline_type!=='student_application')return false
  if(!item.deadline)return status==='open'&&rollingOpenEvidence.test(String(item.status_evidence||''))
  if(!/^\d{4}-\d{2}-\d{2}$/.test(item.deadline))return false
  const end=new Date(item.deadline+'T00:00:00Z')
  if(Number.isNaN(end.getTime())||end.toISOString().slice(0,10)!==item.deadline||item.deadline<indiaToday())return false
  if(item.deadline===indiaToday())return status==='open'||status==='deadline_today'
  return status==='open'
}
function scholarshipPriority(item:Scholarship){
  const hay=`${item.provider||''} ${item.source_name||''} ${item.source_key||''}`.toLowerCase()
  if(hay.includes('life insurance corporation')||hay.includes('lic golden jubilee')||hay.includes(' lic '))return 0
  if(hay.includes('hdfc')||hay.includes('parivartan ecss'))return 1
  if(hay.includes('buddy4study'))return 2
  if(item.is_official||item.source_type==='official')return 10
  return 20
}
function compareScholarships(a:Scholarship,b:Scholarship){
  const priority=scholarshipPriority(a)-scholarshipPriority(b)
  if(priority)return priority
  const aDeadline=Date.parse(a.deadline||'')||Number.MAX_SAFE_INTEGER
  const bDeadline=Date.parse(b.deadline||'')||Number.MAX_SAFE_INTEGER
  return aDeadline-bDeadline
}
function filter(data:ScholarshipFeed,q=''){
  const tokens=q.toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ').filter(Boolean)
  const items=(data.items||[]).filter(isActive).map(item=>item.deadline===indiaToday()&&item.application_status==='open'?{...item,application_status:'deadline_today'}:item).filter(item=>{
    if(!tokens.length)return true
    const hay=[item.title,item.provider,item.source_name,item.source_type,item.region,item.education_level,item.category,item.eligibility,item.academic_year].join(' ').toLowerCase()
    return tokens.every(token=>hay.includes(token))
  }).sort(compareScholarships)
  return {...data,items,count:items.length}
}
async function snapshot(){
  const response=await fetch('/data/scholarships.json',{cache:'force-cache',headers:{Accept:'application/json'}})
  if(!response.ok)throw new Error('Scholarship feed unavailable')
  return await response.json() as ScholarshipFeed
}
export async function fetchScholarships(q=''){
  const apiRequest=api.get('/scholarships/',{params:q?{q}:{}}).then(response=>response.data as ScholarshipFeed)
  try{return filter(await Promise.any([snapshot(),apiRequest]),q)}
  catch{return filter(await apiRequest,q)}
}
export async function fetchScholarship(slug:string){
  const data=await fetchScholarships()
  const item=data.items.find(value=>value.slug===slug)
  if(!item)throw new Error('Scholarship is unavailable or applications have closed.')
  return item
}
export const scholarshipPath=(item:Pick<Scholarship,'slug'>)=>`/scholarships/${item.slug}`
export const scholarshipSourceLabel=(item:Scholarship)=>item.is_official||item.source_type==='official'?`Official source · ${item.source_name}`:`Private / partner listing · ${item.source_name}`
