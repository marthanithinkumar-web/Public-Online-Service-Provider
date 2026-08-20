import React,{useEffect,useState} from 'react'
import {useParams} from 'react-router-dom'
import axios from 'axios'
import {authHeader} from '../../services/auth'

const statuses=['Under Review','Documents Required','In Progress','Completed','Rejected','Cancelled']

export default function AdminOrderDetail(){
 const {id}=useParams();const [data,setData]=useState<any|null>(null);const [status,setStatus]=useState('');const [note,setNote]=useState('');const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');const [error,setError]=useState('')
 const load=async()=>{if(!id)return;setError('');try{const r=await axios.get(`/api/admin/orders/${id}`,{headers:authHeader()});setData(r.data);setStatus(r.data.allowed_next_statuses?.[0]||'')}catch(e:any){setError(e?.response?.data?.error||'Unable to load this request.')}}
 useEffect(()=>{load()},[id])
 const update=async()=>{if(!id||!status)return;setBusy(true);setMessage('');setError('');try{const r=await axios.post(`/api/admin/orders/${id}/status`,{status,note},{headers:authHeader()});setMessage(r.data.message);setNote('');await load()}catch(e:any){setError(e?.response?.data?.error||'Unable to update request status.')}finally{setBusy(false)}}
 if(error&&!data)return <div className="dashboard-state error-state"><h2>Request unavailable</h2><p>{error}</p></div>
 if(!data)return <p>Loading...</p>
 const allowed=data.allowed_next_statuses||statuses
 return <div className="admin-order-detail"><h2>Request {data.order.order_code}</h2><div><strong>Client:</strong> {data.order.client_name} • {data.order.phone}</div><div><strong>Service:</strong> {data.order.service}</div><div><strong>Status:</strong> {data.order.status}</div>
  <section className="dashboard-section"><h3>Process request</h3><p>Move the request only when the corresponding work is actually complete. Add a note when asking for documents or rejecting.</p><label>Next status<select value={status} onChange={e=>setStatus(e.target.value)}><option value="">Select status</option>{allowed.map((s:string)=><option key={s} value={s}>{s}</option>)}</select></label><label>Processing note<textarea rows={4} value={note} onChange={e=>setNote(e.target.value)} placeholder="Tell the client what happened or what is needed…"/></label>{error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button disabled={busy||!status} onClick={update}>{busy?'Updating…':'Update request'}</button></section>
  <h3>Application</h3><div className="request-summary">{Object.entries(data.order.application_data||{}).map(([k,v])=><p key={k}><strong>{k.replace(/_/g,' ')}:</strong> {String(v||'—')}</p>)}</div>
  <h3>History</h3><ul>{data.history.map((h:any)=><li key={h.id}>{new Date(h.created_at).toLocaleString()}: {h.previous_status||'Created'} → {h.new_status} by {h.changed_by}{h.note?` — ${h.note}`:''}</li>)}</ul>
  <h3>Attachments</h3><ul>{data.attachments.map((a:any)=><li key={a.id}>{a.filename}<button onClick={async()=>{try{const r=await fetch(`/api/uploads/${a.id}/download`,{headers:{Authorization:`Bearer ${localStorage.getItem('psp_token')||''}`}});if(!r.ok)throw new Error();const blob=await r.blob();const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=a.filename;link.click();URL.revokeObjectURL(url)}catch{alert('Download failed')}}}>Download</button></li>)}</ul>
  <h3>Grievances</h3><ul>{data.grievances.map((g:any)=><li key={g.id}>{g.grievance_code} — {g.status} — {g.description}</li>)}</ul><h3>Reviews</h3><ul>{data.reviews.map((r:any)=><li key={r.id}>Rating: {r.rating} — {r.comment}</li>)}</ul>
 </div>
}
