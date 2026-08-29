import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const seedPath=path.resolve(scriptDir,'../../backend/seed.py')

export const siteUrl='https://public-online-service-provider-ui.onrender.com'
export const publicRoutes=['/','/jobs','/scholarships','/meeseva','/certificates','/schemes','/about','/contact','/privacy','/terms','/disclaimer']

export function slugify(value){
  return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'service'
}

export function readCatalog(){
  const source=fs.readFileSync(seedPath,'utf8')
  const services=[]
  let category=''
  for(const line of source.split(/\r?\n/)){
    const categoryMatch=line.match(/^\s{4}'([^']+)': \[$/)
    if(categoryMatch){category=categoryMatch[1];continue}
    const tuple=line.match(/^\s*\('((?:\\'|[^'])*)',\s*'((?:\\'|[^'])*)',\s*'((?:\\'|[^'])*)'(?:,\s*([0-9.]+))?\),?$/)
    if(tuple&&category)services.push({
      name:tuple[1].replace(/\\'/g,"'"),
      description:tuple[2].replace(/\\'/g,"'"),
      keywords:tuple[3].replace(/\\'/g,"'"),
      category,
      slug:slugify(tuple[1].replace(/\\'/g,"'")),
    })
  }
  if(services.length<80)throw new Error(`SEO catalog parser found only ${services.length} services; expected at least 80.`)
  const slugs=new Set()
  for(const service of services){
    if(slugs.has(service.slug))throw new Error(`Duplicate public service slug: ${service.slug}`)
    slugs.add(service.slug)
  }
  return services
}
