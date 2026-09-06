import React,{useEffect,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {getSession} from '../../services/session'
import ClientSupportChat from './ClientSupportChat'

export default function SupportChatLauncher(){
  const location=useLocation()
  const session=getSession()
  const [open,setOpen]=useState(false)

  useEffect(()=>setOpen(false),[location.pathname])

  const path=location.pathname
  if(session?.is_admin||path.startsWith('/admin')||path.startsWith('/messages'))return null

  if(!session){
    return <Link className="support-chat-launcher" to="/login?returnTo=%2Fmessages" aria-label="Sign in to open Chat for Support"><span aria-hidden="true">●</span> Chat for Support</Link>
  }

  return <>
    <button className="support-chat-launcher" type="button" aria-expanded={open} aria-controls="floating-support-chat" onClick={()=>setOpen(value=>!value)}><span aria-hidden="true">●</span> {open?'Close chat':'Chat for Support'}</button>
    {open&&<aside className="support-chat-panel" id="floating-support-chat" aria-label="Private support chat">
      <div className="support-chat-panel-header"><div><strong>Chat for Support</strong><small>Private conversation with the service team.</small></div><button type="button" aria-label="Close chat" onClick={()=>setOpen(false)}>×</button></div>
      <ClientSupportChat/>
    </aside>}
  </>
}
