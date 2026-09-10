import React from 'react'
import {useLocation} from 'react-router-dom'
import {buildWhatsAppUrl,currentPageUrl} from '../../services/whatsapp'
import {getSession} from '../../services/session'
import {readCachedServices,slugifyServiceName} from '../../services/serviceCatalog'
import '../../styles/whatsapp.css'

function serviceNameForPath(pathname:string){
  const services=readCachedServices(true)
  const idMatch=pathname.match(/^\/service\/(\d+)/)
  if(idMatch){
    const match=services.find((service:any)=>String(service.id)===idMatch[1])
    return match?.name||match?.catalog_name||undefined
  }
  const slugMatch=pathname.match(/^\/(?:services|recharge-bills)\/([^/?#]+)/)
  if(!slugMatch)return undefined
  const slug=decodeURIComponent(slugMatch[1])
  const match=services.find((service:any)=>[service.slug,slugifyServiceName(service.name||''),slugifyServiceName(service.catalog_name||'')].filter(Boolean).includes(slug))
  return match?.name||match?.catalog_name||slug.replace(/-/g,' ').replace(/\b\w/g,char=>char.toUpperCase())
}

export default function WhatsAppSupportLauncher(){
  const location=useLocation()
  const session=getSession()
  if(session?.is_admin||location.pathname.startsWith('/admin'))return null
  const serviceName=serviceNameForPath(location.pathname)
  const href=buildWhatsAppUrl({topic:serviceName?'Service enquiry':'Website support',serviceName,pageUrl:currentPageUrl()})
  return <a className="whatsapp-support-launcher" href={href} target="_blank" rel="noopener noreferrer" aria-label="Chat with Public Online Service Provider on WhatsApp"><span aria-hidden="true">WA</span> WhatsApp</a>
}
