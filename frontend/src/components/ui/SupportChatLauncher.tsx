import React,{useEffect,useState} from 'react'
import {useLocation} from 'react-router-dom'
import {getSession} from '../../services/session'
import ClientSupportChat from './ClientSupportChat'

export default function SupportChatLauncher(){
  const location=useLocation()
  const session=getSession()
  const [open,setOpen]=useState(false)

  useEffect(()=>setOpen(false),[location.pathname])

  const path=location.pathname
  // Private support chat is available only to authenticated, registered clients.
  // Guests never receive a chat composer; admins use the separate Messages workspace.
  if(!session||session.is_admin||path.startsWith('/admin')||path.startsWith('/messages'))return null

  return <>
    <button className="support-chat-launcher" type="button" aria-expanded={open} aria-controls="floating-support-chat" onClick={()=>setOpen(value=>!value)}><span aria-hidden="true">●</span> {open?'Close chat':'Chat with Admin'}</button>
    {open&&<aside className="support-chat-panel" id="floating-support-chat" aria-label="Private support chat">
      <div className="support-chat-panel-header"><div><strong>Chat with Admin</strong><small>Private messages to the administrator.</small></div><button type="button" aria-label="Close chat" onClick={()=>setOpen(false)}>×</button></div>
      <ClientSupportChat/>
    </aside>}
  </>
}
