import React,{useEffect,useState} from 'react'
import {useParams} from 'react-router-dom'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'

const REQUEST_TIMEOUT_MS = 15000
const statuses=['Under Review','Documents Required','In Progress','Completed','Rejected','Cancelled']

export default function AdminOrderDetail(){
 const {id}=useParams();const [data,setData]=useState<any|null>(null);const [status,setStatus]=useState('');const [note,setNote]=useState('');const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');const [error,setError]=useState('')
 const load=async()=>{if(!id)return;setError('');try{const r=await axios.get(`${apiBase}/admin/orders/${id}`,{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS});setData(r.data);setStatus(r.data.allowed_next_statuses?.[0]||'')}catch(e:any){setError(e?.code==='ECONNABORTED'?'The server took too long to respond. Please try again.':e?.response?.data?.error||'Unable to load this request.')}}
 useEffect(()=>{let active=true;load();return()=>{active=false}},[id])
 const update=async()=>{if(!id||!status)return;setBusy(true);setMessage('');setError('');try{const r=await axios.post(`${apiBase}/admin/orders/${id}/status`,{status,note},{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS});setMessage(r.data.message);setNote('');await load()}catch(e:any){setError(e?.code==='ECONNABORTED'?'The status update timed out. Please try again.':e?.response?.data?.error||'Unable to update request status.')}finally{setBusy(false)}}
 if(error&&!data)return <div className="dashboard-state error-state"><h2>Request unavailable</h2><p>{error}</p><button onClick={load}>Try again</button></div>
 if(!data)return <div className="dashboard-state"><div className="loading-dot"/><p>Loading request...</p></div>
 const allowed=data.allowed_next_statuses||statuses
 const terminal=['Completed','Rejected','Cancelled'].includes(data.order.status)
 return <div className="admin-order-detail"><h2>Request {data.order.order_code}</h2><div><strong>Client:</strong> {data.order.client_name} • {data.order.phone}</div><div><strong>Service:</strong> {data.order.service}</div><div><strong>Status:</strong> {data.order.status}</div>
  {!terminal&&<section className="dashboard-section"><h3>Process request</h3><p>Move the request only when the corresponding work is actually complete. Add a clear client-facing note when asking for documents or closing the request.</p><label>Next status<select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Select status</option>{allowed.map((s:string)=><option key={s} value={s}>{s}</option>)}</select></label><label>Processing note<textarea rows={4} value={note} onChange={e=>setNote(e.target.value)} placeholder="Tell the client what happened or what is needed…"/></label>{error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button disabled={busy||!status}>{busy?'Updating…':'Update request'}</button></section>}
  {terminal&&<p className="info">This request is closed and can no longer be moved to another status.</p>}
  <h3>Application</h3><div className="request-summary">{Object.entries(data.order.application_data||{}).map(([k,v])=><p key={k}><strong>{k.replace(/_/g,' ')}:</strong> {String(v||'—')}</p>)}</div>
  <h3>History</h3><ul>{(data.history||[]).map((h:any)=><li key={h.id}>{new Date(h.created_at).toLocaleString()}: {h.previous_status||'Created'} → {h.new_status} by {h.changed_by}{h.note?` — ${h.note}`:''}</li>)}</ul>
  <h3>Attachments</h3><ul>{(data.attachments||[]).map((a:any)=><li key={a.id}>{a.filename}<button onClick={async()=>{try{const r=await fetch(`${apiBase}/uploads/${a.id}/download`,{headers:authHeader()});if(!r.ok)throw new Error();const contentType=r.headers.get('content-type')||'';if(contentType.includes('application/json')){const body=await r.json();if(body.url){window.open(body.url,'_blank','noopener,noreferrer');return}throw new Error()}const blob=await r.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=a.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{setError('Download failed. Please try again.')}}}>Download</button></li>)}</ul>
  <h3>Grievances</h3><ul>{(data.grievances||[]).map((g:any)=><li key={g.id}>{g.grievance_code} — {g.status} — {g.description}</li>)}</ul><h3>Reviews</h3><ul>{(data.reviews||[]).map((r:any)=><li key={r.id}>Rating: {r.rating} — {r.comment}</li>)}</ul>
 </div>
}
