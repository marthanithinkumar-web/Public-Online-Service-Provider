import {readJobs,readIndexableJobs,readScholarships} from './seo-catalog.mjs'

const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())
const allJobs=readJobs()
const jobs=readIndexableJobs()
const scholarships=readScholarships()
for(const job of allJobs){
  if(job.deadline&&job.deadline<today)throw new Error(`Public job is expired: ${job.slug}`)
  if(!job.deadline){
    const lastSeen=Date.parse(job.last_seen_at||'')
    const age=Date.now()-lastSeen
    if(job.job_type!=='private'||job.source?.allow_missing_deadline!==true||Number(job.confidence||0)<0.8||!Number.isFinite(lastSeen)||age < -5*60*1000||age > 3*24*60*60*1000)throw new Error(`Public undated job is not a recently verified approved private role: ${job.slug}`)
  }
}
for(const job of jobs){
  if(!job.deadline||job.deadline<today)throw new Error(`SEO job is undated or expired: ${job.slug}`)
}
for(const item of scholarships){
  if(!item.deadline||item.deadline<today)throw new Error(`SEO scholarship is undated or expired: ${item.slug}`)
  if(!(item.source_type==='official'||item.is_official===true))throw new Error(`SEO scholarship is not official: ${item.slug}`)
  if(item.stale_source)throw new Error(`SEO scholarship source is stale: ${item.slug}`)
}
console.log(`Verified ${allJobs.length} active public jobs, ${jobs.length} indexable government jobs, and ${scholarships.length} scholarships.`)
