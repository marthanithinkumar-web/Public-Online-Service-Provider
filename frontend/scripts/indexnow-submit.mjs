import { readFile } from 'node:fs/promises'

const enabled=String(process.env.INDEXNOW_SUBMIT||'').trim()==='1'
if(!enabled){
  console.log('IndexNow submission skipped: set INDEXNOW_SUBMIT=1 to opt in.')
  process.exit(0)
}

const key=String(process.env.INDEXNOW_KEY||'30ebc45a8bdddf7660594bcead49f4ad').trim()
let host=''
let keyLocation=''

async function sitemapUrls(){
  try{
    const xml=await readFile(new URL('../public/sitemap.xml',import.meta.url),'utf8')
    return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match=>match[1]).filter(url=>{
      try{return new URL(url).host===host}catch{return false}
    }).slice(0,10000)
  }catch(error){
    console.warn('IndexNow sitemap read skipped:',error instanceof Error?error.message:String(error))
    return []
  }
}

try{
  const configuredOrigin=String(process.env.INDEXNOW_SITE_URL||process.env.VITE_SITE_URL||'https://pospindia.onrender.com').trim()
  host=new URL(configuredOrigin).host
  if(!host)throw new Error('IndexNow site origin has no hostname')
  keyLocation=`https://${host}/${key}.txt`
  const urlList=await sitemapUrls()
  if(!urlList.length){
    console.warn('IndexNow submission skipped: sitemap has no URLs for configured host.')
    process.exit(0)
  }
  const response=await fetch('https://api.indexnow.org/indexnow',{
    method:'POST',
    headers:{'content-type':'application/json'},
    body:JSON.stringify({host,key,keyLocation,urlList})
  })
  const body=await response.text()
  const output=`IndexNow submission: ${response.status} ${response.statusText}; URLs=${urlList.length}${body?`; body=${body.slice(0,200)}`:''}`
  if(response.ok)console.log(output)
  else console.warn(output)
}catch(error){
  console.warn('IndexNow submission skipped:',error instanceof Error?error.message:String(error))
}
