import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {publicRoutes,readCatalog,readJobs,readScholarships,siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const publicDir=path.resolve(scriptDir,'../public')
const services=readCatalog()
const jobs=readJobs()
const scholarships=readScholarships()
const urls=[
  ...publicRoutes,
  ...services.map(service=>`/services/${service.slug}`),
  ...jobs.map(job=>`/jobs/${job.slug}`),
  ...scholarships.map(item=>`/scholarships/${item.slug}`),
]
if(new Set(urls).size!==urls.length)throw new Error('Duplicate public URL generated for sitemap.xml')
const xml=`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(route=>`  <url><loc>${siteUrl}${route}</loc></url>`).join('\n')}\n</urlset>\n`
const robots=`User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /my-orders\nDisallow: /account-settings\nDisallow: /messages\nDisallow: /grievances\nDisallow: /submit-grievance\nDisallow: /submit-review\nDisallow: /reset-password\nDisallow: /login\nDisallow: /register\nDisallow: /request-reset\nDisallow: /verify\n\nSitemap: ${siteUrl}/sitemap.xml\n`

fs.writeFileSync(path.join(publicDir,'sitemap.xml'),xml)
fs.writeFileSync(path.join(publicDir,'robots.txt'),robots)
fs.writeFileSync(path.join(publicDir,'seo-catalog.json'),`${JSON.stringify(services,null,2)}\n`)
console.log(`Generated sitemap with ${urls.length} public URLs for ${siteUrl}.`)
