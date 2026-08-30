import {useEffect} from 'react'

const SITE_URL='https://public-online-service-provider.onrender.com'
const SITE_NAME='Public Online Service Provider'
const DEFAULT_DESCRIPTION='Independent assistance for PAN cards, certificates, government jobs, scholarships, schemes, MeeSeva and other public-service applications.'

type Schema=Record<string,unknown>|Record<string,unknown>[]

function setMeta(selector:string,attributes:Record<string,string>){
  let element=document.head.querySelector(selector) as HTMLMetaElement|null
  if(!element){element=document.createElement('meta');document.head.appendChild(element)}
  Object.entries(attributes).forEach(([key,value])=>element!.setAttribute(key,value))
}

export function canonicalUrl(pathname:string){
  const path=pathname==='/'?'/':`/${pathname.replace(/^\/+|\/+$/g,'')}`
  return `${SITE_URL}${path}`
}

export default function Seo({title,description=DEFAULT_DESCRIPTION,path='/',index=true,type='website',schema}:{title:string;description?:string;path?:string;index?:boolean;type?:string;schema?:Schema}){
  useEffect(()=>{
    const fullTitle=title.includes(SITE_NAME)?title:`${title} | ${SITE_NAME}`
    const canonical=canonicalUrl(path)
    document.title=fullTitle
    document.documentElement.lang='en-IN'
    setMeta('meta[name="description"]',{name:'description',content:description})
    setMeta('meta[name="robots"]',{name:'robots',content:index?'index,follow,max-image-preview:large':'noindex,nofollow,noarchive'})
    setMeta('meta[property="og:title"]',{property:'og:title',content:fullTitle})
    setMeta('meta[property="og:description"]',{property:'og:description',content:description})
    setMeta('meta[property="og:type"]',{property:'og:type',content:type})
    setMeta('meta[property="og:url"]',{property:'og:url',content:canonical})
    setMeta('meta[property="og:site_name"]',{property:'og:site_name',content:SITE_NAME})
    setMeta('meta[name="twitter:card"]',{name:'twitter:card',content:'summary'})
    setMeta('meta[name="twitter:title"]',{name:'twitter:title',content:fullTitle})
    setMeta('meta[name="twitter:description"]',{name:'twitter:description',content:description})
    let link=document.head.querySelector('link[rel="canonical"]') as HTMLLinkElement|null
    if(!link){link=document.createElement('link');link.rel='canonical';document.head.appendChild(link)}
    link.href=canonical
    let script=document.getElementById('structured-data') as HTMLScriptElement|null
    if(schema){
      if(!script){script=document.createElement('script');script.id='structured-data';script.type='application/ld+json';document.head.appendChild(script)}
      script.text=JSON.stringify(schema)
    }else{script?.remove()}
  },[title,description,path,index,type,schema])
  return null
}

export const SITE={url:SITE_URL,name:SITE_NAME,description:DEFAULT_DESCRIPTION}
