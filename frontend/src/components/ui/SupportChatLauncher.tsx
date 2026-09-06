import React from 'react'
import {Link,useLocation} from 'react-router-dom'
import {getSession} from '../../services/session'

export default function SupportChatLauncher(){
  const location=useLocation()
  const session=getSession()
  const path=location.pathname

  if(session?.is_admin||path.startsWith('/admin')||path.startsWith('/messages'))return null

  const destination=session?'/messages':`/login?returnTo=${encodeURIComponent('/messages')}`
  return <Link className="support-chat-launcher" to={destination} aria-label="Chat with Admin"><span aria-hidden="true">●</span> Chat with Admin</Link>
}
