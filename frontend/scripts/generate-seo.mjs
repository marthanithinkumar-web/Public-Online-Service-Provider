import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {publicRoutes,readCatalog,siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const publicDir=path.resolve(scriptDir,'../public')
const services=readCatalog()
const urls=[...publicRoutes,...services.map(service=>`/services/${service.slug}`)]
const xml=`<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(route=>`  <url><loc>${siteUrl}${route}</loc></url>`).join('\n')}\n</urlset>\n`

fs.writeFileSync(path.join(publicDir,'sitemap.xml'),xml)
fs.writeFileSync(path.join(publicDir,'seo-catalog.json'),`${JSON.stringify(services,null,2)}\n`)
console.log(`Generated sitemap with ${urls.length} public URLs.`)
