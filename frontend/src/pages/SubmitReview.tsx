import React,{useState} from 'react'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {authHeader} from '../services/auth'
import {Link,useSearchParams} from 'react-router-dom'

export default function SubmitReview(){
 const [params]=useSearchParams();const [form,setForm]=useState({order_id:params.get('order_id')||'',rating:5,comment:''});const [msg,setMsg]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false)
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setMsg('');setError('');setBusy(true);try{const payload:any={rating:Number(form.rating),comment:form.comment};if(form.order_id)payload.order_id=Number(form.order_id);const r=await axios.post(`${apiBase}/reviews`,payload,{headers:authHeader()});setMsg(r.data.message)}catch(err:any){setError(err?.response?.data?.error||'We could not submit your review. Please try again.')}finally{setBusy(false)}}
 return <div className="form-page"><div className="form-hero"><span className="eyebrow">Your feedback</span><h1>Review a completed service</h1><p>Your feedback helps us improve the experience.</p></div><div className="form-card"><form onSubmit={submit} className="request-form"><label>Related Request ID<input value={form.order_id} onChange={e=>setForm({...form,order_id:e.target.value})} required/></label><label>Rating (1–5)<input type="number" min={1} max={5} value={form.rating} onChange={e=>setForm({...form,rating:Number(e.target.value)})}/></label><label>Comment<textarea required minLength={5} rows={6} value={form.comment} onChange={e=>setForm({...form,comment:e.target.value})}/></label>{error&&<p className="info" role="alert">{error}</p>}{msg&&<p className="success-message" role="status">{msg}</p>}<button type="submit" disabled={busy}>{busy?'Submitting…':'Submit review'}</button></form></div><p className="form-back"><Link to="/my-orders">← Back to my requests</Link></p></div>
}
