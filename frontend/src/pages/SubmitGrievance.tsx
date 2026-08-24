import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {authHeader} from '../services/auth'
import {Link,useSearchParams} from 'react-router-dom'

export default function SubmitGrievance(){
 const [params]=useSearchParams();const [form,setForm]=useState({order_id:params.get('order_id')||'',description:''});const [msg,setMsg]=useState('');const [busy,setBusy]=useState(false);const [error,setError]=useState('')
 const submit=async(e:React.FormEvent)=>{e.preventDefault();if(busy)return;setMsg('');setError('');setBusy(true);try{const payload:any={description:form.description};if(form.order_id)payload.order_id=Number(form.order_id);const r=await axios.post(`${apiBase}/grievances/`,payload,{headers:authHeader()});setMsg(r.data.message+(r.data.grievance?` Code: ${r.data.grievance.grievance_code}`:''));setForm({order_id:'',description:''})}catch(err:any){setError(err?.response?.data?.error||'We could not submit your grievance. Please try again.')}finally{setBusy(false)}}
 return <div className="form-page"><div className="form-hero"><span className="eyebrow">Support</span><h1>Get help with a request</h1><p>Tell us what went wrong or what you need from the service team.</p></div><div className="form-card"><form onSubmit={submit} className="request-form"><label>Related Request ID<input value={form.order_id} onChange={e=>setForm({...form,order_id:e.target.value})} placeholder="Optional"/></label><label>Describe the issue<textarea value={form.description} required minLength={10} rows={7} onChange={e=>setForm({...form,description:e.target.value})}/></label>{error&&<p className="info" role="alert">{error}</p>}{msg&&<p className="success-message" role="status">{msg}</p>}<button type="submit" disabled={busy}>{busy?'Submitting…':'Submit grievance'}</button></form></div><p className="form-back"><Link to="/my-orders">← Back to my requests</Link></p></div>
}
