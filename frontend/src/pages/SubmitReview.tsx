import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'
import { Link } from 'react-router-dom'

export default function SubmitReview(){
  const [form,setForm]=useState({order_id:'',rating:5,comment:'',client_name:''}); const [msg,setMsg]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false)
  const submit=async(e:React.FormEvent)=>{e.preventDefault();setMsg('');setError('');setBusy(true);try{const payload:any={rating:Number(form.rating),comment:form.comment};if(form.order_id)payload.order_id=Number(form.order_id);if(form.client_name)payload.client_name=form.client_name;const res=await axios.post(`${apiBase}/reviews`,payload);setMsg(res.data.message);setForm({order_id:'',rating:5,comment:'',client_name:''})}catch(err:any){setError(err?.response?.data?.error||'We could not submit your review. Please try again.')}finally{setBusy(false)}}
  return <div className="form-page"><div className="form-hero"><span className="eyebrow">Your feedback</span><h1>Share a service review</h1><p>Your feedback helps us improve the experience for everyone using public-service assistance.</p></div><div className="form-card"><form onSubmit={submit} className="request-form">
    <label>Related Order ID (optional)<input value={form.order_id} onChange={e=>setForm({...form,order_id:e.target.value})}/></label>
    <label>Rating (1–5)<input type="number" min={1} max={5} value={form.rating} onChange={e=>setForm({...form,rating:Number(e.target.value)})}/></label>
    <label>Comment<textarea required minLength={5} rows={6} value={form.comment} onChange={e=>setForm({...form,comment:e.target.value})}/></label>
    <label>Your name (optional)<input value={form.client_name} onChange={e=>setForm({...form,client_name:e.target.value})}/></label>
    {error&&<p className="info" role="alert">{error}</p>}{msg&&<p className="success-message" role="status">{msg}</p>}
    <button type="submit" disabled={busy}>{busy?'Submitting…':'Submit review'}</button>
  </form></div><p className="form-back"><Link to="/my-orders">← Back to my requests</Link></p></div>
}
