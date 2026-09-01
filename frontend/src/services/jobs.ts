import axios from 'axios'
import {apiBase} from './apiBase'

export type JobSource={key:string;name:string;listing_url:string;last_sync_completed_at?:string|null;last_sync_status?:string;fetched_count?:number;published_count?:number;last_error?:string|null;enabled?:boolean}
export type JobNotification={
  id:number;slug:string;title:string;organization:string;job_type:'government'|'private';appointment_type?:string|null;
  location?:string|null;qualification?:string|null;age_limit?:string|null;application_fee?:string|null;vacancies?:string|null;
  salary?:string|null;summary?:string|null;issue_date?:string|null;application_start_date?:string|null;deadline?:string|null;
  official_notice_url:string;application_url?:string|null;status:string;verification_status:string;is_featured:boolean;
  source?:JobSource|null;first_seen_at?:string|null;last_seen_at?:string|null;published_at?:string|null;confidence?:number;
}

const api=axios.create({baseURL:apiBase,timeout:15000})

export async function fetchJobs(params:Record<string,string|number|boolean>={}){
  return (await api.get('/jobs/',{params})).data as {items:JobNotification[];count:number}
}

export async function fetchJob(slug:string){
  return (await api.get(`/jobs/${encodeURIComponent(slug)}`)).data as {job:JobNotification}
}

export async function fetchJobSources(){
  return (await api.get('/jobs/sources')).data as {items:JobSource[]}
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
