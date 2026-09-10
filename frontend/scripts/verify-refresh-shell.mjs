import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {readCatalog,readJobs,readScholarships,readStartupDefaultServices,siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const distDir=path.resolve(scriptDir,'../dist')
const [sampleJob]=readJobs()
const [sampleScholarship]=readScholarships()
const startupServices=readStartupDefaultServices()
const requiredPages=[
  'index.html',
  'government-services/index.html',
  'recharge-bills/index.html',
  'jobs/index.html',
  'scholarships/index.html',
  'services/apply-government-job',
  'services/residence-certificate',
  `jobs/${sampleJob.slug}`,
  `scholarships/${sampleScholarship.slug}`,
]
const legacyEmploymentNewsUrl='https://employmentnews.gov.in/NewEmp/AllJobs.aspx?k=All'

for(const relative of requiredPages){
  const target=path.join(distDir,relative)
  if(!fs.existsSync(target)) throw new Error(`Missing refresh target: ${relative}`)
  const html=fs.readFileSync(target,'utf8')
  if(!html.includes('<script src="/app-boot.js"></script>')) throw new Error(`Missing CSP-safe app bootstrap in ${relative}`)
  if(html.includes("<script>document.documentElement.classList.add('js')</script>")) throw new Error(`Inline app bootstrap regressed in ${relative}`)
  if(!html.includes(`<link rel="canonical" href="${siteUrl}`)) throw new Error(`Canonical URL is not using ${siteUrl} in ${relative}`)
}

const jobsHtml=fs.readFileSync(path.join(distDir,'jobs/index.html'),'utf8')
if(jobsHtml.includes(legacyEmploymentNewsUrl)) throw new Error('Removed Employment News All Jobs URL leaked into the prerendered jobs page')

const robots=fs.readFileSync(path.join(distDir,'robots.txt'),'utf8')
if(!robots.includes(`Sitemap: ${siteUrl}/sitemap.xml`)) throw new Error('robots.txt sitemap does not use the configured site URL')
if(!robots.includes('Disallow: /admin\n')) throw new Error('robots.txt does not protect the exact /admin route')
if(robots.includes('Disallow: /admin/\n')) throw new Error('robots.txt only protects /admin children, not the exact route')

const sitemap=fs.readFileSync(path.join(distDir,'sitemap.xml'),'utf8')
if(!sitemap.includes(`<loc>${siteUrl}/</loc>`)) throw new Error('sitemap.xml does not use the configured site URL')
if(!sitemap.includes(`<loc>${siteUrl}/government-services</loc>`)) throw new Error('Service directory is missing from sitemap.xml')
if(!sitemap.includes(`<loc>${siteUrl}/jobs/${sampleJob.slug}</loc>`)) throw new Error('Job detail URLs are missing from sitemap.xml')
if(!sitemap.includes(`<loc>${siteUrl}/scholarships/${sampleScholarship.slug}</loc>`)) throw new Error('Scholarship detail URLs are missing from sitemap.xml')

const catalog=JSON.parse(fs.readFileSync(path.join(distDir,'seo-catalog.json'),'utf8'))
const catalogSlugs=new Set(readCatalog().map(service=>service.slug))
for(const service of startupServices){
  if(!catalogSlugs.has(service.slug)||!catalog.some(item=>item.slug===service.slug)) throw new Error(`Startup service is missing from SEO catalog: ${service.slug}`)
  if(!sitemap.includes(`<loc>${siteUrl}/services/${service.slug}</loc>`)) throw new Error(`Startup service is missing from sitemap.xml: ${service.slug}`)
}

if(!fs.existsSync(path.join(distDir,'googlededa399e0c0b6df4.html'))) throw new Error('Google Search Console verification file was not copied to dist')
if(!fs.existsSync(path.join(distDir,'app-boot.js'))) throw new Error('app-boot.js was not copied to dist')
console.log(`Verified refresh shell, SEO origin ${siteUrl}, Search Console verification, and removed legacy job source.`)
