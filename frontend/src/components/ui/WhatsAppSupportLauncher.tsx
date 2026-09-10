import React from 'react'
import {useLocation} from 'react-router-dom'
import {buildWhatsAppUrl,currentPageUrl} from '../../services/whatsapp'
import {getSession} from '../../services/session'

export default function WhatsAppSupportLauncher(){
  const location=useLocation()
  const session=getSession()
  if(session?.is_admin||location.pathname.startsWith('/admin'))return null
  const href=buildWhatsAppUrl({topic:'Website support',pageUrl:currentPageUrl()})
  return <a className="whatsapp-support-launcher" href={href} target="_blank" rel="noopener noreferrer" aria-label="Chat with Public Online Service Provider on WhatsApp"><span aria-hidden="true">WA</span> WhatsApp</a>
}
