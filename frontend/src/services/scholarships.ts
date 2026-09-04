import axios from 'axios'
import {apiBase} from './apiBase'

export type ScholarshipSourceHealth={ok:boolean;source_name?:string;source_url?:string;count?:number;checked_at?:string;elapsed_ms?:number;error?:string}
export type Scholarship={
  id:string;slug:string;title:string;provider:string;source_name:string;source_url:string;application_url:string;
  deadline?:string|null;award?:string|null;region?:string|null;education_level?:string|null;income_limit?:string|null;
  category?:string|null;eligibility?:string|null;documents?:string[];status?:string;verified_at?:string|null;
  source_type?:'official'|'private';is_official?:boolean;source_key?:string;record_type?:'scholarship'|'official_notice';
  academic_year?:string|null;last_seen_at?:string|null;stale_source?:boolean;discovery_method?:string
}
export type ScholarshipFeed={
  items:Scholarship[];count:number;generated_at?:string|null;official_count?:number;private_count?:number;stale_source_count?:number;
  discovery?:{mode?:string;checked_at?:string;source_health?:Record<string,ScholarshipSourceHealth>}
}

const api=axios.create({baseURL:apiBase,timeout:5000})
const isActive=(item:Scholarship)=>{
  if(item.status&&item.status!=='active')return false
  if(!item.deadline)return true
  const end=new Date(`${item.deadline}T23:59:59`)
  return Number.isNaN(end.getTime())||end.getTime()>=Date.now()
}
function filter(data:ScholarshipFeed,q=''){
  const tokens=q.toLowerCase().replace(/[^a-z0-9]+/g,' ').split(' ').filter(Boolean)
  const items=(data.items||[]).filter(isActive).filter(item=>{
    if(!tokens.length)return true
    const hay=[item.title,item.provider,item.source_name,item.source_type,item.region,item.education_level,item.category,item.eligibility,item.academic_year].join(' ').toLowerCase()
    return tokens.every(token=>hay.includes(token))
  })
  return {...data,items,count:items.length}
}
async function snapshot(){
  const response=await fetch('/data/scholarships.json',{cache:'force-cache',headers:{Accept:'application/json'}})
  if(!response.ok)throw new Error('Scholarship feed unavailable')
  return await response.json() as ScholarshipFeed
}
export async function fetchScholarships(q=''){
  try{return filter((await api.get('/scholarships/',{params:q?{q}:{}})).data as ScholarshipFeed,q)}
  catch{return filter(await snapshot(),q)}
}
export async function fetchScholarship(slug:string){
  const data=await fetchScholarships()
  const item=data.items.find(value=>value.slug===slug)
  if(!item)throw new Error('Scholarship is unavailable or applications have closed.')
  return item
}
export const scholarshipPath=(item:Pick<Scholarship,'slug'>)=>`/scholarships/${item.slug}`
export const scholarshipSourceLabel=(item:Scholarship)=>item.is_official||item.source_type==='official'?`Official source · ${item.source_name}`:`Private / partner listing · ${item.source_name}`
