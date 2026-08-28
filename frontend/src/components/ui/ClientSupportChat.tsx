import React,{useEffect,useRef,useState} from 'react'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'

const TIMEOUT_MS=15000

export default function ClientSupportChat(){
 const [items,setItems]=useState<any[]>([]);const [message,setMessage]=useState('');const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const endRef=useRef<HTMLDivElement|null>(null)
 const load=async()=>{setError('');try{const response=await axios.get(`${apiBase}/messages/mine`,{headers:authHeader(),timeout:TIMEOUT_MS});setItems(response.data.items||[]);if(response.data.unread)await axios.post(`${apiBase}/messages/mine/read`,{}, {headers:authHeader(),timeout:TIMEOUT_MS})}catch{setError('Private messages are temporarily unavailable. Please try again.')}finally{setLoading(false)}}
 useEffect(()=>{load();const timer=window.setInterval(load,10000);return()=>window.clearInterval(timer)},[])
 useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth',block:'nearest'})},[items.length])
 const send=async(event:React.FormEvent)=>{event.preventDefault();const text=message.trim();if(!text||busy)return;setBusy(true);setError('');try{const response=await axios.post(`${apiBase}/messages/mine`,{message:text},{headers:authHeader(),timeout:TIMEOUT_MS});setItems(current=>[...current,response.data.item]);setMessage('')}catch(err:any){setError(err?.response?.data?.error||'Your message could not be sent. Please try again.')}finally{setBusy(false)}}
 return <section className="dashboard-section support-chat" id="support-messages" aria-labelledby="support-chat-title">
  <div className="section-header inline"><div><span className="eyebrow">Private support</span><h2 id="support-chat-title">Message the service team</h2><p>Ask a question without leaving your dashboard. Replies appear here and in notifications.</p></div><button className="btn btn-secondary small" type="button" onClick={()=>{setLoading(true);load()}} disabled={loading}>Refresh</button></div>
  <div className="chat-safety-note"><strong>Keep your account safe:</strong> Never send OTPs, passwords, PINs, CVV numbers or banking-login details.</div>
  <div className="chat-thread" aria-live="polite">
   {loading?<p className="chat-empty">Loading messages…</p>:items.length===0?<p className="chat-empty">No messages yet. Send a question and the service team can reply from the admin workspace.</p>:items.map(item=><article key={item.id} className={`chat-bubble ${item.sender_role==='client'?'chat-client':'chat-admin'}`}><strong>{item.sender_role==='client'?'You':'Service team'}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small></article>)}
   <div ref={endRef}/>
  </div>
  {error&&<p className="info" role="alert">{error}</p>}
  <form className="chat-composer" onSubmit={send}><label htmlFor="client-support-message">Your message</label><div><textarea id="client-support-message" rows={3} maxLength={2000} value={message} onChange={event=>setMessage(event.target.value)} placeholder="How can we help?"/><button type="submit" disabled={busy||!message.trim()}>{busy?'Sending…':'Send message'}</button></div><small>{message.length}/2000</small></form>
 </section>
}
