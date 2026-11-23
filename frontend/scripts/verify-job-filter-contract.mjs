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
  ['current explicit deadline state',/function deadlineState\(job:JobNotification\)/],
  ['deadline closes after its date',/if\(deadline<local\.date\)return 'closed'/],
  ['same-day cutoff closes at the official minute',/if\(cutoff&&local\.time\.slice\(0,5\)>=cutoff\)return 'closed'/],
  ['fresh official source verification',/function sourceIsFresh\(job:JobNotification\)/],
  ['public feed requires fresh source and deadline state',/function isVerifiedPublicJob\(job:JobNotification\)[\s\S]*?sourceIsFresh\(job\)[\s\S]*?deadlineState\(job\)/],
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
  ['deadline and sorting controls',/Closing within 7 days[\s\S]*Newest notices/],
  ['clear filters control',/clearFilters/],
  ['pagination controls',/Page \{page\} of \{pageCount\}/],
]){
  if(!pattern.test(page))throw new Error(`Jobs UI filter is not wired: ${name}`)
}
for(const [name,pattern] of [
  ['read-only snapshot source',/_read_snapshot\(\)\['items'\]/],
  ['published status gate',/raw\.get\('status'\) != 'published'/],
  ['verified application status gate',/raw\.get\('application_status'\) not in \{'open', 'deadline_today'\}/],
  ['official verification gate',/raw\.get\('verification_status'\) != 'official_source_checked'/],
  ['successful source gate',/source\.get\('last_sync_status'\).*success/],
  ['fresh successful source timestamp',/_is_fresh_timestamp\(source\.get\('last_successful_sync_at'/],
  ['official deadline timezone and cutoff',/ZoneInfo\(timezone_name\)[\s\S]*?deadline_cutoff_time/],
  ['duplicate slug suppression',/seen_slugs/],
  ['HTTPS official notice and application links',/notice_url\.startswith\('https:\/\/'\)[\s\S]*?application_url\.startswith\('https:\/\/'\)/],
  ['bounded API limit',/min\(100, max\(1, int\(request\.args\.get\('limit', 30\)\)\)\)/],
]){
  if(!pattern.test(api))throw new Error('Backend read-only job snapshot contract missing: '+name)
}
if(/JobNotification\.query|JobSource\.query|db\.session|trigger_background_sync/.test(api)){
  throw new Error('Public job API must not access the production database or trigger background sync')
}
if(!/hashlib\.sha256\(_SNAPSHOT_PATH\.read_bytes\(\)\)/.test(api)){
  throw new Error('Snapshot status must verify the deployed JSON against its SHA-256 marker')
}
console.log('Verified read-only job snapshot API, official deadline/freshness gates, search, type, featured, detail, sources and limit.')
