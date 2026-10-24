import {readIndexableJobs,readScholarships} from './seo-catalog.mjs'

const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date())
const jobs=readIndexableJobs()
const scholarships=readScholarships()
for(const job of jobs){
  if(!job.deadline||job.deadline<today)throw new Error(`SEO job is undated or expired: ${job.slug}`)
}
for(const item of scholarships){
  if(!item.deadline||item.deadline<today)throw new Error(`SEO scholarship is undated or expired: ${item.slug}`)
  if(!(item.source_type==='official'||item.is_official===true))throw new Error(`SEO scholarship is not official: ${item.slug}`)
  if(item.stale_source)throw new Error(`SEO scholarship source is stale: ${item.slug}`)
}
console.log(`Verified SEO eligibility for ${jobs.length} jobs and ${scholarships.length} scholarships.`)
