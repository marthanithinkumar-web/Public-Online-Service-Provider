import { readFile } from 'node:fs/promises'

const key='30ebc45a8bdddf7660594bcead49f4ad'
const host='pospindia.onrender.com'
const keyLocation=`https://${host}/${key}.txt`

async function sitemapUrls(){
  try{
    const xml=await readFile(new URL('../public/sitemap.xml',import.meta.url),'utf8')
    return [...xml.matchAll(/<loc>([^<]+)<\/loc>/g)].map(match=>match[1]).filter(url=>{
      try{return new URL(url).host===host}catch{return false}
    }).slice(0,10000)
  }catch(error){
    console.warn('IndexNow sitemap read skipped:',error instanceof Error?error.message:String(error))
    return [`https://${host}/`]
  }
}

try{
  const urlList=await sitemapUrls()
  if(!urlList.length)urlList.push(`https://${host}/`)
  const response=await fetch('https://api.indexnow.org/indexnow',{
    method:'POST',
    headers:{'content-type':'application/json'},
    body:JSON.stringify({host,key,keyLocation,urlList})
  })
  const body=await response.text()
  console.log(`IndexNow submission: ${response.status} ${response.statusText}; URLs=${urlList.length}${body?`; body=${body.slice(0,200)}`:''}`)
}catch(error){
  console.warn('IndexNow submission skipped:',error instanceof Error?error.message:String(error))
}
