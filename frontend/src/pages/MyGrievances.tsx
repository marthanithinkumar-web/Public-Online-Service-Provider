import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {Link} from 'react-router-dom'
import ClientWorkspaceNav from '../components/ui/ClientWorkspaceNav'
import {apiBase} from '../services/apiBase'
import {authHeader} from '../services/auth'

export default function MyGrievances(){
  const [items,setItems]=useState<any[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('')
  const load=async()=>{setLoading(true);setError('');try{const response=await axios.get(`${apiBase}/grievances/mine`,{headers:authHeader(),timeout:15000});setItems(response.data.items||[])}catch(err:any){setError(err?.code==='ECONNABORTED'?'Grievances took too long to load. Please try again.':err?.response?.data?.error||'Unable to load your grievances.')}finally{setLoading(false)}}
  useEffect(()=>{load()},[])
  return <div className="client-workspace-shell"><ClientWorkspaceNav/><div className="client-dashboard">
    <section className="dashboard-hero"><div><span className="eyebrow">Private support</span><h1>My grievances</h1><p>Track support requests, provider responses and every important status update.</p></div><Link className="btn btn-primary" to="/submit-grievance">Submit grievance</Link></section>
    {loading?<div className="dashboard-state" role="status"><div className="loading-dot"/><p>Loading grievances…</p></div>:error?<div className="dashboard-state error-state" role="alert"><h2>Grievances unavailable</h2><p>{error}</p><button onClick={load}>Try again</button></div>:items.length===0?<section className="dashboard-section empty-dashboard"><h2>No grievances</h2><p>If you need help, submit a private grievance linked to one of your requests or choose general support.</p><Link className="btn btn-primary" to="/submit-grievance">Get support</Link></section>:<div className="request-list">{items.map(item=><article className="request-card" key={item.id}><div className="request-card-main"><div className="request-icon">G</div><div><div className="request-code">{item.grievance_code}</div><h2>{item.order_code?`Request ${item.order_code}`:'General support'}</h2><p>{item.description}</p></div></div><div className="request-card-side"><span className={`status-pill status-${String(item.status).toLowerCase().replace(/\s+/g,'-')}`}>{item.status}</span><small>Updated {new Date(item.updated_at||item.created_at).toLocaleString()}</small></div>{item.admin_response&&<div className="request-summary"><strong>Provider response</strong><p>{item.admin_response}</p></div>}<div className="request-timeline">{(item.history||[]).map((entry:any)=><div className="timeline-item active" key={entry.id}><strong>{entry.new_status}</strong><span>{new Date(entry.created_at).toLocaleString()}</span>{entry.note&&<small>{entry.note}</small>}</div>)}</div>{item.order_id&&<div className="request-card-actions"><Link to={`/my-orders/${item.order_id}`}>View related application</Link></div>}</article>)}</div>}
  </div></div>
}
