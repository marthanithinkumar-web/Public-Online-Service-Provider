import React,{useEffect,useRef,useState} from 'react'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'

const TIMEOUT_MS=15000
const POLL_INTERVAL_MS=20000

export default function ClientSupportChat(){
 const [items,setItems]=useState<any[]>([]);const [message,setMessage]=useState('');const [loading,setLoading]=useState(true);const [busy,setBusy]=useState(false);const [error,setError]=useState('');const endRef=useRef<HTMLDivElement|null>(null);const loadingRequest=useRef(false);const mounted=useRef(true)
 const load=async()=>{
  // Prevent slow API responses from stacking up when the server is waking or the
  // network is unreliable. A single in-flight refresh is enough for this thread.
  if(loadingRequest.current)return
  loadingRequest.current=true
  try{
   const response=await axios.get(`${apiBase}/messages/mine`,{headers:authHeader(),timeout:TIMEOUT_MS})
   if(!mounted.current)return
   setItems(Array.isArray(response.data.items)?response.data.items:[])
   setError('')
   if(response.data.unread){
    await axios.post(`${apiBase}/messages/mine/read`,{}, {headers:authHeader(),timeout:TIMEOUT_MS})
   }
  }catch{
   if(mounted.current)setError('Private messages are temporarily unavailable. Check your connection and try again.')
  }finally{
   loadingRequest.current=false
   if(mounted.current)setLoading(false)
  }
 }
 useEffect(()=>{
  mounted.current=true
  void load()
  const timer=window.setInterval(()=>{if(document.visibilityState==='visible')void load()},POLL_INTERVAL_MS)
  const onVisible=()=>{if(document.visibilityState==='visible')void load()}
  document.addEventListener('visibilitychange',onVisible)
  return()=>{mounted.current=false;window.clearInterval(timer);document.removeEventListener('visibilitychange',onVisible)}
 },[])
 useEffect(()=>{endRef.current?.scrollIntoView({behavior:'smooth',block:'nearest'})},[items.length])
 const send=async(event:React.FormEvent)=>{
  event.preventDefault();const text=message.trim();if(!text||busy)return
  setBusy(true);setError('')
  try{
   const response=await axios.post(`${apiBase}/messages/mine`,{message:text},{headers:authHeader(),timeout:60000})
   if(!mounted.current)return
   setItems(current=>[...current,response.data.item,...(response.data.ai_item?[response.data.ai_item]:[])])
   setMessage('')
   // The send endpoint confirms the saved message; refresh shortly afterwards
   // to reconcile server ordering and any reply that arrived during submission.
   window.setTimeout(()=>{if(mounted.current)void load()},500)
  }catch(err:any){
   if(mounted.current)setError(err?.response?.data?.error||'Your message could not be sent. Check your connection and try again.')
  }finally{if(mounted.current)setBusy(false)}
 }
 return <section className="dashboard-section support-chat" id="support-messages" aria-labelledby="support-chat-title">
  <div className="section-header inline"><div><span className="eyebrow">Private support</span><h2 id="support-chat-title">Message the service team</h2><p>POSP AI can answer routine questions here; a human administrator can take over when needed.</p></div><button className="btn btn-secondary small" type="button" onClick={()=>{setLoading(true);void load()}} disabled={loading}>Refresh</button></div>
  <div className="chat-safety-note"><strong>Keep your account safe:</strong> Never send OTPs, passwords, PINs, CVV numbers or banking-login details.</div>
  <div className="chat-thread" aria-live="polite">
   {loading?<p className="chat-empty">Loading messages…</p>:items.length===0?<p className="chat-empty">No messages yet. Ask a question and POSP AI or the service team will reply here.</p>:items.map(item=><article key={item.id} className={`chat-bubble ${item.sender_role==='client'?'chat-client':'chat-admin'}`}><strong>{item.sender_role==='client'?'You':item.sender_role==='ai'?'POSP AI':'Service team'}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small></article>)}
   <div ref={endRef}/>
  </div>
  {error&&<p className="info" role="alert">{error}</p>}
  <form className="chat-composer" onSubmit={send}><label htmlFor="client-support-message">Your message</label><div><textarea id="client-support-message" rows={3} maxLength={2000} value={message} onChange={event=>setMessage(event.target.value)} placeholder="How can we help?"/><button type="submit" disabled={busy||!message.trim()}>{busy?'Sending…':'Send message'}</button></div><small>{message.length}/2000</small></form>
 </section>
}
