import {PROVIDER} from './config'

type WhatsAppContext = {
  serviceName?: string | null
  requestReference?: string | number | null
  topic?: string | null
  pageUrl?: string | null
}

function normalizedNumber(){
  const configured=String(PROVIDER.whatsapp||PROVIDER.phone||'').replace(/\D/g,'')
  if(configured.length===10)return `91${configured}`
  return configured
}

export function buildWhatsAppMessage(context:WhatsAppContext={}){
  const lines=['Hello, I need help with Public Online Service Provider.']
  if(context.topic)lines.push(`Topic: ${String(context.topic).trim()}`)
  if(context.serviceName)lines.push(`Service: ${String(context.serviceName).trim()}`)
  if(context.requestReference)lines.push(`Request reference: ${String(context.requestReference).trim()}`)
  if(context.pageUrl)lines.push(`Page: ${String(context.pageUrl).trim()}`)
  return lines.join('\n')
}

export function buildWhatsAppUrl(context:WhatsAppContext={}){
  const number=normalizedNumber()
  const message=buildWhatsAppMessage(context)
  return `https://wa.me/${number}?text=${encodeURIComponent(message)}`
}

export function currentPageUrl(){
  if(typeof window==='undefined')return undefined
  return window.location.href
}
