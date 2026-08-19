import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'
import { Link } from 'react-router-dom'

export default function SubmitGrievance(){
  const [form, setForm] = useState({ order_id:'', client_name:'', phone:'', email:'', description:'' })
  const [msg, setMsg] = useState(''); const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  const submit = async (e:React.FormEvent)=>{
    e.preventDefault(); setMsg(''); setError(''); setBusy(true)
    try{
      const payload:any={client_name:form.client_name,phone:form.phone,description:form.description}
      if(form.order_id) payload.order_id=Number(form.order_id); if(form.email) payload.email=form.email
      const res=await axios.post(`${apiBase}/grievances`,payload)
      setMsg(res.data.message + (res.data.grievance ? ` Code: ${res.data.grievance.grievance_code}` : ''))
      setForm({order_id:'',client_name:'',phone:'',email:'',description:''})
    }catch(err:any){setError(err?.response?.data?.error||'We could not submit your grievance. Please try again.')}finally{setBusy(false)}
  }
  return <div className="form-page"><div className="form-hero"><span className="eyebrow">Support</span><h1>Submit a grievance</h1><p>Tell us what went wrong with a service request and our team can review it.</p></div><div className="form-card"><form onSubmit={submit} className="request-form">
    <label>Related Order ID (optional)<input value={form.order_id} onChange={e=>setForm({...form,order_id:e.target.value})} /></label>
    <label>Full name<input value={form.client_name} required onChange={e=>setForm({...form,client_name:e.target.value})} /></label>
    <label>Phone<input type="tel" value={form.phone} required onChange={e=>setForm({...form,phone:e.target.value})} /></label>
    <label>Email (optional)<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})} /></label>
    <label>Describe the issue<textarea value={form.description} required minLength={10} rows={6} onChange={e=>setForm({...form,description:e.target.value})}/></label>
    {error&&<p className="info" role="alert">{error}</p>}{msg&&<p className="success-message" role="status">{msg}</p>}
    <button type="submit" disabled={busy}>{busy?'Submitting…':'Submit grievance'}</button>
  </form></div><p className="form-back"><Link to="/my-orders">← Back to my requests</Link></p></div>
}
