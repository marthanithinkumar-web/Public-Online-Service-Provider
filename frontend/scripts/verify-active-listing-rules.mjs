import {readIndexableJobs,readScholarships} from './seo-catalog.mjs'

function localParts(timeZone='Asia/Kolkata'){
  const parts=new Intl.DateTimeFormat('en-CA',{timeZone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date())
  const value=Object.fromEntries(parts.map(part=>[part.type,part.value]))
  return {date:`${value.year}-${value.month}-${value.day}`,time:`${value.hour}:${value.minute}`}
}
const rollingEvidence=/\b(?:currently accepting applications|applications? (?:are )?(?:currently )?open|open for applications|registration\b.{0,80}\b(?:is|are)\s+(?:currently\s+)?open|application process is open)\b/i
const jobs=readIndexableJobs()
const scholarships=readScholarships()
for(const job of jobs){
  const local=localParts(job.deadline_timezone||'Asia/Kolkata')
  if(!job.deadline||job.deadline<=local.date)throw new Error(`SEO job is undated, expired or due today: ${job.slug}`)
}
for(const item of scholarships){
  if(!(item.source_type==='official'||item.is_official===true))throw new Error(`SEO scholarship is not official: ${item.slug}`)
  if(item.stale_source)throw new Error(`SEO scholarship source is stale: ${item.slug}`)
  if(!item.deadline){
    if(item.application_status!=='open'||!rollingEvidence.test(String(item.status_evidence||'')))throw new Error(`SEO scholarship has no verified rolling-open evidence: ${item.slug}`)
    continue
  }
  const local=localParts(item.deadline_timezone||'Asia/Kolkata')
  if(item.deadline<local.date)throw new Error(`SEO scholarship is expired: ${item.slug}`)
  if(item.deadline===local.date){
    if(item.application_status!=='deadline_today')throw new Error(`SEO scholarship deadline-today status is missing: ${item.slug}`)
    const cutoff=String(item.deadline_cutoff_time||'').slice(0,5)
    if(cutoff&&local.time>=cutoff)throw new Error(`SEO scholarship passed its official cutoff: ${item.slug}`)
  }else if(item.application_status!=='open'){
    throw new Error(`SEO scholarship future deadline is not marked open: ${item.slug}`)
  }
}
console.log(`Verified SEO eligibility for ${jobs.length} jobs and ${scholarships.length} scholarships.`)
