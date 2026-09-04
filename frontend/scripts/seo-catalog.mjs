import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const seedPath=path.resolve(scriptDir,'../../backend/seed.py')

export const siteUrl='https://public-online-service-provider-india.onrender.com'
export const publicRoutes=['/','/jobs','/scholarships','/meeseva','/certificates','/schemes','/about','/contact','/privacy','/terms','/disclaimer']

const extraServices=[
  ['Mobile Postpaid Bill Payment Assistance','Assistance with postpaid mobile bill details and request tracking for supported Indian operators. The bill amount is separate from the website assistance fee and payment authorization remains with the client.','mobile postpaid,postpaid bill,mobile bill,airtel postpaid,jio postpaid,vi postpaid,bsnl postpaid,telecom bill,bill payment','Recharge & Bill Payments'],
  ['DTH Recharge Assistance','Assistance with DTH recharge details, plan selection and request tracking. The DTH recharge amount is separate from the website assistance fee and payment authorization remains with the client.','dth recharge,tata play,airtel digital tv,dish tv,d2h,videocon d2h,sun direct,tv recharge,recharge','Recharge & Bill Payments'],
  ['Broadband / Landline Bill Payment Assistance','Assistance with broadband or landline bill details and request tracking. The provider bill amount is separate from the website assistance fee and payment authorization remains with the client.','broadband bill,landline bill,internet bill,fiber bill,airtel xstream,jiofiber,bsnl broadband,act fibernet,bill payment','Recharge & Bill Payments'],
  ['FASTag Recharge Assistance','Assistance with FASTag recharge details and request tracking. The FASTag recharge amount is separate from the website assistance fee and payment authorization remains with the client.','fastag recharge,fast tag,toll recharge,vehicle tag,nhai,highway toll,recharge','Recharge & Bill Payments'],
  ['Piped Gas Bill Payment Assistance','Assistance with piped-gas bill details and request tracking. The gas bill amount is separate from the website assistance fee and payment authorization remains with the client.','piped gas bill,gas bill,png bill,city gas,consumer number,bill payment,utility','Recharge & Bill Payments'],
]

export function slugify(value){
  return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')||'service'
}

export function applicationServiceName(value){
  const name=String(value||'').trim()
  if(!name)return name
  if(name.toLowerCase().startsWith('apply '))return `Apply ${name.slice(6).trim()}`
  if(name.toLowerCase().endsWith(' order apply'))return name.slice(0,-' Apply'.length)
  if(name.toLowerCase().endsWith(' apply'))return `Apply ${name.slice(0,-' Apply'.length).trim()}`
  for(const suffix of [' Application Assistance',' Service Assistance',' Assistance',' Guidance'])if(name.endsWith(suffix)){
    const base=name.slice(0,-suffix.length).trim()
    return base.toLowerCase().endsWith(' order')?base:`Apply ${base}`
  }
  return name
}

export function readCatalog(){
  const source=fs.readFileSync(seedPath,'utf8')
  const services=[]
  let category=''
  for(const line of source.split(/\r?\n/)){
    const categoryMatch=line.match(/^\s{4}'([^']+)': \[$/)
    if(categoryMatch){category=categoryMatch[1];continue}
    const tuple=line.match(/^\s*\('((?:\\'|[^'])*)',\s*'((?:\\'|[^'])*)',\s*'((?:\\'|[^'])*)'(?:,\s*([0-9.]+))?\),?$/)
    if(tuple&&category){const name=applicationServiceName(tuple[1].replace(/\\'/g,"'"));services.push({
      name,
      description:tuple[2].replace(/\\'/g,"'"),
      keywords:tuple[3].replace(/\\'/g,"'"),
      category,
      slug:slugify(name),
    })}
  }
  const existingSlugs=new Set(services.map(service=>service.slug))
  for(const [catalogName,description,keywords,extraCategory] of extraServices){
    const name=applicationServiceName(catalogName)
    const slug=slugify(name)
    if(!existingSlugs.has(slug)){
      services.push({name,description,keywords,category:extraCategory,slug})
      existingSlugs.add(slug)
    }
  }
  if(services.length<80)throw new Error(`SEO catalog parser found only ${services.length} services; expected at least 80.`)
  const slugs=new Set()
  for(const service of services){
    if(slugs.has(service.slug))throw new Error(`Duplicate public service slug: ${service.slug}`)
    if(/\sApply$/i.test(service.name))throw new Error(`Legacy trailing-Apply service title generated: ${service.name}`)
    slugs.add(service.slug)
  }
  return services
}
