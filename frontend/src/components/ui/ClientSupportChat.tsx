import React,{useEffect,useRef,useState} from 'react'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'

const TIMEOUT_MS=15000

export default function ClientSupportChat(){
 const [items,setItems]=useState<any[]>([]);const [message,setMessage]=useState('');const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const [notice,setNotice]=useState('');const endRef=useRef<HTMLDivElement|null>(null)
 const load=async()=>{try{const response=await axios.get(`${apiBase}/messages/mine`,{headers:authHeader(),timeout:TIMEOUT_MS});setItems(response.data.items||[]);if(response.data.unread)await axios.post(`${apiBase}/messages/mine/read`,{}, {headers:authHeader(),timeout:TIMEOUT_MS})}catch{setError('Private messages are temporarily unavailable. Please try again.')}finally{setLoading(false)}}
 useEffect(()=>{load();const timer=window.setInterval(load,10000);return()=>window.clearInterval(timer)},[])
 useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth',block:'nearest'})},[items.length])
 const send=async(event:React.FormEvent)=>{event.preventDefault();const text=message.trim();if(!text||busy)return;setBusy(true);setError('');setNotice('');try{const response=await axios.post(`${apiBase}/messages/mine`,{message:text},{headers:authHeader(),timeout:60000});setItems(current=>[...current,response.data.item,...(response.data.ai_item?[response.data.ai_item]:[])]);setMessage('');if(response.data.ai_error){setNotice(`Your message was saved, but POSP AI could not reply: ${response.data.ai_error} The service team has been notified.`)}else if(response.data.ai_handoff){setNotice('Your message was sent to the service team. A human administrator may need to reply here.')}else{setNotice('POSP AI replied in this chat.')}}catch(err:any){setError(err?.response?.data?.error||'Your message could not be sent. Please try again.')}finally{setBusy(false)}}
 return <section className="dashboard-section support-chat" id="support-messages" aria-labelledby="support-chat-title">
  <div className="section-header inline"><div><span className="eyebrow">Private support</span><h2 id="support-chat-title">Message the service team</h2><p>POSP AI can answer routine questions here; a human administrator can take over when needed.</p></div><button className="btn btn-secondary small" type="button" onClick={()=>{setLoading(true);setError('');load()}} disabled={loading}>Refresh</button></div>
  <div className="chat-safety-note"><strong>Keep your account safe:</strong> Never send OTPs, passwords, PINs, CVV numbers or banking-login details.</div>
  <div className="chat-thread" aria-live="polite">
   {loading?<p className="chat-empty">Loading messages…</p>:items.length===0?<p className="chat-empty">No messages yet. Ask a question and POSP AI or the service team will reply here.</p>:items.map(item=><article key={item.id} className={`chat-bubble ${item.sender_role==='client'?'chat-client':'chat-admin'}`}><strong>{item.sender_role==='client'?'You':item.sender_role==='ai'?'POSP AI':'Service team'}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small></article>)}
   <div ref={endRef}/>
  </div>
  {error&&<p className="info" role="alert">{error}</p>}
  {notice&&<p className="info" role="status">{notice}</p>}
  <form className="chat-composer" onSubmit={send}><label htmlFor="client-support-message">Your message</label><div><textarea id="client-support-message" rows={3} maxLength={2000} value={message} onChange={event=>setMessage(event.target.value)} placeholder="How can we help?"/><button type="submit" disabled={busy||!message.trim()}>{busy?'Waiting for reply…':'Send message'}</button></div><small>{message.length}/2000</small></form>
 </section>
}
