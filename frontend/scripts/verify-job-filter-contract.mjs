import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {dirname,resolve} from 'node:path'

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..')
const read=path=>readFileSync(resolve(root,path),'utf8')
const service=read('frontend/src/services/jobs.ts')
const page=read('frontend/src/pages/Jobs.tsx')
const api=read('backend/app/routes/jobs.py')
const seo=read('frontend/scripts/seo-catalog.mjs')
const card=read('frontend/src/components/jobs/JobCard.tsx')
const detail=read('frontend/src/pages/JobDetail.tsx')

const required=[
  ['published status',/job\.status==='published'/],
  ['cutoff and verification-aware public eligibility',/isPubliclyActiveJob\(job\)/],
  ['source success requirement',/job\.source\?\.last_sync_status==='success'/],
  ['36-hour source freshness',/SOURCE_FRESHNESS_MS=36\*60\*60\*1000/],
  ['deadline-today warning',/Deadline today—check official portal/],
  ['exact same-day cutoff',/indiaTime\(now,timeZone\)>=cutoff/],
  ['government/private type',/job\.job_type!==type/],
  ['featured flag',/!job\.is_featured/],
  ['search all normalized tokens',/tokens\.every\(token=>searchable\.includes\(token\)\)/],
  ['bounded limit',/Math\.min\(100,Math\.max\(1,requested\)\)/],
  ['source name/key searchable in snapshot',/job\.source\?\.name,job\.source\?\.key/],
]
for(const [name,pattern] of required){
  if(!pattern.test(service))throw new Error(`Job filter contract missing: ${name}`)
}
for(const [name,pattern] of [
  ['search form submission',/onSubmit=\{submit\}/],
  ['government filter control',/setType\('government'\)/],
  ['private filter control',/setType\('private'\)/],
  ['all filter control',/setType\(''\)/],
]){
  if(!pattern.test(page))throw new Error(`Jobs UI filter is not wired: ${name}`)
}
for(const [name,pattern] of [
  ['public current-deadline base query',/JobNotification\.deadline\.isnot\(None\)/],
  ['exact same-day cutoff query',/JobNotification\.deadline_cutoff_time > cutoff/],
  ['successful official source only',/JobSource\.last_sync_status == 'success'/],
  ['fresh item observation',/JobNotification\.last_seen_at >= freshness_cutoff/],
  ['type filter',/JobNotification\.job_type == job_type/],
  ['featured filter',/JobNotification\.is_featured\.is_\(True\)/],
  ['search source name/key',/JobNotification\.source\.has\(or_\(/],
  ['bounded API limit',/min\(100, max\(1, int\(request\.args\.get\('limit', 30\)\)\)\)/],
]){
  if(!pattern.test(api))throw new Error(`Backend job filter missing: ${name}`)
}
for(const [name,pattern] of [
  ['SEO current cutoff and source freshness',/hasCurrentJobDeadline\(item\)/],
  ['job cards suppress uncertain apply action',/canApply\?['"]View Details & Apply['"]/],
  ['job detail suppresses assistance when not verified open',/canApply\?/],
]){
  const source=name.startsWith('SEO')?seo:name.startsWith('job cards')?card:detail
  if(!pattern.test(source))throw new Error(`Job publication contract missing: ${name}`)
}
console.log('Verified job filter contract: India deadline/cutoff, fresh official source, API, UI, search and SEO.')
