import fs from 'node:fs'
import path from 'node:path'
import {fileURLToPath} from 'node:url'
import {publicRoutes,readJobs,readScholarships,siteUrl} from './seo-catalog.mjs'

const scriptDir=path.dirname(fileURLToPath(import.meta.url))
const distDir=path.resolve(scriptDir,'../dist')
const defaultSiteUrl='https://pospindia.onrender.com'
const template=fs.readFileSync(path.join(distDir,'index.html'),'utf8').replaceAll(defaultSiteUrl,siteUrl)
const services=JSON.parse(fs.readFileSync(path.join(distDir,'seo-catalog.json'),'utf8'))
const jobs=readJobs()
const scholarships=readScholarships()
const escapeHtml=value=>String(value||'').replace(/[&<>"']/g,char=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]))
const safeHttpsUrl=value=>{try{const url=new URL(String(value||''));return url.protocol==='https:'?url.href:'#'}catch{return '#'}}

// Keep the crawlable homepage canonical, Open Graph URL and structured-data
// URLs aligned with the same deployment-time site URL used by the sitemap.
fs.writeFileSync(path.join(distDir,'index.html'),template)

const categoryPages={
  '/government-services':{title:'Government Services — Application Assistance',description:'Browse all available government and public-service assistance options in one easy directory.',match:value=>!/recharge & bill payments/i.test(value)},
  '/recharge-bills':{title:'Recharge & Bill Payments — Assistance',description:'Browse available recharge and bill-payment assistance options in one easy directory.',match:value=>/recharge & bill payments/i.test(value)},
  '/jobs':{title:'Government Jobs & Recruitment Notices',description:'Review current government and private recruitment notices gathered from approved official sources, with deadlines and important details where available.',match:value=>/job|employment|exam/i.test(value)},
  '/scholarships':{title:'Scholarship Application Assistance',description:'Explore independent application help for eligible scholarships, renewals and scholarship status checks.',match:value=>/scholarship|student welfare/i.test(value)},
  '/meeseva':{title:'MeeSeva and Online Public Service Assistance',description:'Find independent assistance for eligible MeeSeva and other online public-service applications.',match:value=>/online public service|meeseva/i.test(value)},
  '/certificates':{title:'Government Certificate Application Assistance',description:'Explore help with eligible income, caste, residence, birth, death and other certificate applications.',match:value=>/certificate|public document/i.test(value)},
  '/schemes':{title:'Government Scheme Application Assistance',description:'Explore independent eligibility and application assistance for government schemes and welfare services.',match:value=>/scheme|welfare/i.test(value)},
}

const informationPages={
  '/about':{title:'About Public Online Service Provider',description:'Learn how Public Online Service Provider offers private, independent assistance for public-service applications.'},
  '/contact':{title:'Contact Public Online Service Provider',description:'Contact Public Online Service Provider for help choosing an available public-service assistance option.'},
  '/privacy':{title:'Privacy Policy',description:'Read how Public Online Service Provider handles account, request and service information.'},
  '/terms':{title:'Terms and Conditions',description:'Read the terms that apply when using Public Online Service Provider.'},
  '/disclaimer':{title:'Independent Provider Disclaimer',description:'Public Online Service Provider is an independent private assistance platform, not a government department or official portal.'},
}

function schemaMarkup(value){return JSON.stringify(value).replace(/</g,'\\u003c')}
function pageHtml({route,title,description,body,schema}){
  const fullTitle=title.includes('Public Online Service Provider')?title:`${title} | Public Online Service Provider`
  const canonical=`${siteUrl}${route}`
  let html=template
    .replace(/<title>.*?<\/title>/s,`<title>${escapeHtml(fullTitle)}</title>`)
    .replace(/<meta name="description"[^>]*>/,`<meta name="description" content="${escapeHtml(description)}" />`)
    .replace(/<link rel="canonical"[^>]*>/,`<link rel="canonical" href="${canonical}" />`)
    .replace(/<meta property="og:title"[^>]*>/,`<meta property="og:title" content="${escapeHtml(fullTitle)}" />`)
    .replace(/<meta property="og:description"[^>]*>/,`<meta property="og:description" content="${escapeHtml(description)}" />`)
    .replace(/<meta property="og:url"[^>]*>/,`<meta property="og:url" content="${canonical}" />`)
    .replace(/<script id="structured-data" type="application\/ld\+json">.*?<\/script>/s,`<script id="structured-data" type="application/ld+json">${schemaMarkup(schema)}</script>`)
    .replace(/<!--seo-snapshot-start-->.*?<!--seo-snapshot-end-->/s,`<!--seo-snapshot-start--><main class="container page-content seo-snapshot">${body}</main><!--seo-snapshot-end-->`)
  return html
}

for(const [route,page] of Object.entries(categoryPages)){
  const links=services.filter(service=>page.match(service.category)).map(service=>`<li><a href="/services/${service.slug}">${escapeHtml(service.name)}</a> — ${escapeHtml(service.description)}</li>`).join('')
  const sourceLinks=route==='/jobs'?`<h2>Priority official job sources</h2><ul><li><a href="https://ssc.gov.in/">Staff Selection Commission</a></li><li><a href="https://rrcb.gov.in/">Railway Recruitment Control Board</a></li><li><a href="https://www.upsc.gov.in/recruitment/recruitment-advertisement">Union Public Service Commission</a></li><li><a href="https://opportunities.rbi.org.in/Scripts/Vacancies.aspx">Reserve Bank of India</a></li><li><a href="https://sbi.co.in/web/careers/current-openings">State Bank of India</a></li><li><a href="https://navodaya.gov.in/nvs/en/Recruitment/">Navodaya Vidyalaya Samiti</a></li><li><a href="https://sainikschoolsociety.in/">Sainik Schools Society</a></li></ul><p>Notices are checked daily. Incomplete or ambiguous records are held for administrator review instead of being published.</p>`:''
  const body=`<article><p>Independent private assistance platform — not a government department or official portal.</p><h1>${escapeHtml(page.title)}</h1><p>${escapeHtml(page.description)}</p>${sourceLinks}<h2>Available assistance services</h2><ul>${links}</ul><p><a href="/">Search all public services</a></p></article>`
  const schema={'@context':'https://schema.org','@type':'CollectionPage',name:page.title,url:`${siteUrl}${route}`,description:page.description,isPartOf:{'@type':'WebSite',name:'Public Online Service Provider',url:siteUrl}}
  const target=path.join(distDir,route.slice(1),'index.html');fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,pageHtml({route,...page,body,schema}))
}

for(const [route,page] of Object.entries(informationPages)){
  const body=`<article><p>Public Online Service Provider</p><h1>${escapeHtml(page.title)}</h1><p>${escapeHtml(page.description)}</p><p>We provide independent private assistance and do not represent a government department or official government portal.</p><p><a href="${route}">Read this page</a> · <a href="/">Return home</a></p></article>`
  const schema={'@context':'https://schema.org','@type':'WebPage',name:page.title,url:`${siteUrl}${route}`,description:page.description,isPartOf:{'@type':'WebSite',name:'Public Online Service Provider',url:siteUrl}}
  const target=path.join(distDir,route.slice(1),'index.html');fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,pageHtml({route,...page,body,schema}))
}

for(const service of services){
  const route=`/services/${service.slug}`
  const title=`${service.name} Assistance`
  const description=`${service.description} Review assistance requirements, documents, fees and the request process.`
  const body=`<article><p><a href="/">Home</a> / ${escapeHtml(service.category)}</p><h1>${escapeHtml(service.name)} Assistance</h1><p>${escapeHtml(service.description)}</p><h2>Purpose and eligibility</h2><p>We provide independent form-filling and application guidance. Eligibility, availability and approval are decided under the applicable official rules.</p><h2>Documents and fees</h2><p>Review the relevant identity, eligibility or supporting documents before applying. The website shows our assistance fee separately from any government or official charge.</p><h2>Application process</h2><ol><li>Create or sign in to your client account.</li><li>Review the service information and provide relevant details.</li><li>Review fees and submit the request.</li><li>Track updates using your request reference.</li></ol><p>Never share OTPs, passwords, PINs, CVV or banking-login credentials.</p><p><a href="${route}">Open this service and continue</a></p></article>`
  const schema=[{'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:siteUrl},{'@type':'ListItem',position:2,name:service.category,item:`${siteUrl}/#services`},{'@type':'ListItem',position:3,name:service.name,item:`${siteUrl}${route}`}]},{'@context':'https://schema.org','@type':'Service',name:service.name,description:service.description,serviceType:service.category,provider:{'@type':'Organization',name:'Public Online Service Provider',url:siteUrl},areaServed:{'@type':'Country',name:'India'},url:`${siteUrl}${route}`}]
  const target=path.join(distDir,'services',service.slug);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,pageHtml({route,title,description,body,schema}))
}

for(const job of jobs){
  const route=`/jobs/${job.slug}`
  const title=`${job.title} — ${job.organization||'Recruitment notice'}`
  const description=job.summary||`Review this verified recruitment notice from ${job.organization||'the published official source'}.`
  const facts=[['Organization',job.organization],['Location',job.location],['Qualification',job.qualification],['Age limit',job.age_limit],['Vacancies',job.vacancies],['Salary',job.salary],['Deadline',job.deadline]].filter(([,value])=>Boolean(value)).map(([label,value])=>`<li><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</li>`).join('')
  const officialUrl=safeHttpsUrl(job.official_notice_url)
  const body=`<article><p><a href="/">Home</a> / <a href="/jobs">Jobs</a></p><h1>${escapeHtml(job.title)}</h1><p><strong>${escapeHtml(job.organization)}</strong></p><p>${escapeHtml(description)}</p><h2>Notice details</h2><ul>${facts}</ul><p>Read the authoritative eligibility, reservation, fee and document requirements in the linked official notice before applying.</p>${officialUrl==='#'?'':`<p><a href="${escapeHtml(officialUrl)}">View official notification</a></p>`}<p><a href="${route}">Open this job notice</a></p></article>`
  const schema={'@context':'https://schema.org','@type':'WebPage',name:title,url:`${siteUrl}${route}`,description,isPartOf:{'@type':'WebSite',name:'Public Online Service Provider',url:siteUrl}}
  const target=path.join(distDir,'jobs',job.slug);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,pageHtml({route,title,description,body,schema}))
}

for(const item of scholarships){
  const route=`/scholarships/${item.slug}`
  const title=item.title
  const description=`${item.provider||item.source_name||'Scholarship provider'} scholarship eligibility, deadline and application assistance.`
  const facts=[['Provider',item.provider],['Study level',item.education_level],['Region',item.region],['Category',item.category],['Academic year',item.academic_year],['Deadline',item.deadline]].filter(([,value])=>Boolean(value)).map(([label,value])=>`<li><strong>${escapeHtml(label)}:</strong> ${escapeHtml(value)}</li>`).join('')
  const sourceUrl=safeHttpsUrl(item.source_url)
  const body=`<article><p><a href="/">Home</a> / <a href="/scholarships">Scholarships</a></p><h1>${escapeHtml(item.title)}</h1><p>${escapeHtml(description)}</p><h2>Eligibility and details</h2><ul>${facts}</ul><p>${escapeHtml(item.eligibility||'Confirm the current scheme-specific eligibility conditions in the linked source before applying.')}</p>${sourceUrl==='#'?'':`<p><a href="${escapeHtml(sourceUrl)}">View source details</a></p>`}<p><a href="${route}">Open this scholarship</a></p></article>`
  const schema={'@context':'https://schema.org','@type':'WebPage',name:title,url:`${siteUrl}${route}`,description,isPartOf:{'@type':'WebSite',name:'Public Online Service Provider',url:siteUrl}}
  const target=path.join(distDir,'scholarships',item.slug);fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,pageHtml({route,title,description,body,schema}))
}

console.log(`Pre-rendered ${publicRoutes.length+services.length+jobs.length+scholarships.length} crawlable public pages for ${siteUrl}.`)
