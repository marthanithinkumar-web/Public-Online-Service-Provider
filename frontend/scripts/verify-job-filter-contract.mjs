import {readFileSync} from 'node:fs'
import {fileURLToPath} from 'node:url'
import {dirname,resolve} from 'node:path'

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..')
const read=path=>readFileSync(resolve(root,path),'utf8')
const service=read('frontend/src/services/jobs.ts')
const page=read('frontend/src/pages/Jobs.tsx')
const api=read('backend/app/routes/jobs.py')

const required=[
  ['published status',/job\.status!=='published'/],
  ['current explicit deadline',/hasCurrentDeadline\(job\.deadline\)/],
  ['government/private type',/job\.job_type!==type/],
  ['featured flag',/!job\.is_featured/],
  ['search all normalized tokens',/tokens\.every\(token=>searchable\.includes\(token\)\)/],
  ['bounded limit',/Math\.min\(100,Math\.max\(1,requested\)\)/],
  ['source name/key searchable in snapshot',/job\.source\?\.name,job\.source\?\.key/],
  ['location/state filter',/String\(job\.location\|\|''\)\.toLowerCase\(\)\.includes\(location\)/],
  ['qualification/education filter',/String\(job\.qualification\|\|''\)\.toLowerCase\(\)\.includes\(qualification\)/],
  ['deadline windows',/deadline==='closing_soon'/],
  ['pagination',/slice\(\(page-1\)\*limit,page\*limit\)/],
]
for(const [name,pattern] of required){
  if(!pattern.test(service))throw new Error(`Job filter contract missing: ${name}`)
}
for(const [name,pattern] of [
  ['search form submission',/onSubmit=\{submit\}/],
  ['government filter control',/updateFilters\(\{type:'government'\}\)/],
  ['private filter control',/updateFilters\(\{type:'private'\}\)/],
  ['all filter control',/updateFilters\(\{type:''\}\)/],
  ['location and qualification controls',/id="job-location"[\s\S]*id="job-qualification"/],
  ['featured control',/Featured only/],
  ['deadline and sorting controls',/Closing within 7 days[\s\S]*Recently published/],
  ['clear filters control',/clearFilters/],
  ['pagination controls',/Page \{page\} of \{Math\.ceil\(total\/PAGE_SIZE\)\}/],
]){
  if(!pattern.test(page))throw new Error(`Jobs UI filter is not wired: ${name}`)
}
for(const [name,pattern] of [
  ['public current-deadline base query',/JobNotification\.deadline\.isnot\(None\)/],
  ['type filter',/JobNotification\.job_type == job_type/],
  ['featured filter',/JobNotification\.is_featured\.is_\(True\)/],
  ['search source name/key',/JobNotification\.source\.has\(or_\(/],
  ['location/state filter',/JobNotification\.location\.ilike/],
  ['qualification/education filter',/JobNotification\.qualification\.ilike/],
  ['deadline window filter',/deadline_filter == 'closing_soon'/],
  ['pagination offset',/offset\(\(page - 1\) \* limit\)/],
  ['bounded API limit',/min\(100, max\(1, int\(request\.args\.get\('limit', 30\)\)\)\)/],
]){
  if(!pattern.test(api))throw new Error(`Backend job filter missing: ${name}`)
}
console.log('Verified job filter contract: active deadline, search, source, type, location, qualification, featured, sorting and pagination.')
