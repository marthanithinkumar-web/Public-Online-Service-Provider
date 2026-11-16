import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const root=path.resolve(scriptDir,'../..')
const robotsPath=path.resolve(scriptDir,'../public/robots.txt')
const robots=fs.readFileSync(robotsPath,'utf8')
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
console.log('Verified crawlable robots.txt and X-Robots-Tag noindex coverage for '+privateRoutes.length+' private route patterns.')
