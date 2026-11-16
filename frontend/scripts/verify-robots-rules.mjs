import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {jobRouteSlug, readIndexableJobs, readScholarships, siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const root=path.resolve(scriptDir,'../..')
const robotsPath=path.resolve(scriptDir,'../public/robots.txt')
const sitemapPath=path.resolve(scriptDir,'../public/sitemap.xml')
const robots=fs.readFileSync(robotsPath,'utf8')
const sitemap=fs.readFileSync(sitemapPath,'utf8')
const render=fs.readFileSync(path.resolve(root,'render.yaml'),'utf8')
const lines=new Set(robots.split(/\r?\n/))
const privateRoutes=[
  '/admin',
  '/admin/*',
  '/my-orders',
  '/my-orders/*',
  '/account-settings',
  '/messages',
  '/grievances',
  '/submit-*',
  '/login',
  '/register',
  '/request-*',
  '/reset-password',
  '/verify',
]
for(const route of privateRoutes){
  const expected='- path: '+route+'\n        name: X-Robots-Tag\n        value: noindex, nofollow, noarchive'
  if(!render.includes(expected))throw new Error('Render noindex header is missing for private route: '+route)
}
if(!lines.has('User-agent: *'))throw new Error('robots.txt is missing the global user-agent group')
if(!lines.has('Allow: /'))throw new Error('robots.txt is missing the public-route allow rule')
if(!lines.has('Sitemap: '+siteUrl+'/sitemap.xml'))throw new Error('robots.txt is missing the canonical sitemap URL')
if([...lines].some(line=>line.startsWith('Disallow: '))){
  throw new Error('robots.txt must allow crawlers to read private-route X-Robots-Tag noindex headers')
}

const sitemapUrls=[...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map(([,url])=>url.trim())
if(!sitemapUrls.length)throw new Error('Generated sitemap contains no canonical URLs')
if(new Set(sitemapUrls).size!==sitemapUrls.length)throw new Error('Generated sitemap contains duplicate URLs')
const expectedJobs=new Set(readIndexableJobs().map(item=>siteUrl+'/jobs/'+jobRouteSlug(item)))
const expectedScholarships=new Set(readScholarships().map(item=>siteUrl+'/scholarships/'+item.slug))
const actualJobs=new Set(sitemapUrls.filter(url=>url.startsWith(siteUrl+'/jobs/')))
const actualScholarships=new Set(sitemapUrls.filter(url=>url.startsWith(siteUrl+'/scholarships/')))
const sameSet=(left,right)=>left.size===right.size&&[...left].every(value=>right.has(value))
if(!sameSet(actualJobs,expectedJobs)){
  const missing=[...expectedJobs].filter(url=>!actualJobs.has(url))
  const unexpected=[...actualJobs].filter(url=>!expectedJobs.has(url))
  throw new Error('Job sitemap eligibility mismatch. Missing: '+missing.join(', ')+'; unexpected: '+unexpected.join(', '))
}
if(!sameSet(actualScholarships,expectedScholarships)){
  const missing=[...expectedScholarships].filter(url=>!actualScholarships.has(url))
  const unexpected=[...actualScholarships].filter(url=>!expectedScholarships.has(url))
  throw new Error('Scholarship sitemap eligibility mismatch. Missing: '+missing.join(', ')+'; unexpected: '+unexpected.join(', '))
}
console.log('Verified crawlable robots.txt, '+privateRoutes.length+' private noindex route patterns, '+actualJobs.size+' eligible job details and '+actualScholarships.size+' eligible scholarship details in the generated sitemap.')
