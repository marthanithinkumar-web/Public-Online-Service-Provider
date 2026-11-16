import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const robotsPath=path.resolve(scriptDir,'../public/robots.txt')
const robots=fs.readFileSync(robotsPath,'utf8')
const lines=new Set(robots.split(/\r?\n/))
const privateRoutes=[
  '/login',
  '/register',
  '/admin',
  '/request-reset',
  '/reset-password',
  '/my-orders',
  '/account-settings',
  '/messages',
  '/grievances',
  '/submit-grievance',
  '/submit-review',
]
for(const route of privateRoutes){
  if(!lines.has(\`Disallow: \${route}\`))throw new Error(\`robots.txt is missing private-route exclusion: \${route}\`)
}
if(!lines.has('User-agent: *'))throw new Error('robots.txt is missing the global user-agent group')
if(!lines.has('Allow: /'))throw new Error('robots.txt is missing the public-route allow rule')
if(!lines.has(\`Sitemap: \${siteUrl}/sitemap.xml\`))throw new Error('robots.txt is missing the canonical sitemap URL')
if(lines.has('Disallow: /'))throw new Error('robots.txt must not block the entire public website')
console.log(\`Verified robots exclusions for \${privateRoutes.length} private route prefixes.\`)
