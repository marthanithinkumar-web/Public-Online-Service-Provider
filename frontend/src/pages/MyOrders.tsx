import React, {useEffect, useMemo, useState} from 'react'
import axios from 'axios'
import {Link} from 'react-router-dom'
import {authHeader} from '../services/auth'
import {apiBase} from '../services/apiBase'

export default function MyOrders(){
 const [orders,setOrders]=useState<any[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('')
 const load=async()=>{setLoading(true);setError('');try{const r=await axios.get(`${apiBase}/orders/mine`,{headers:authHeader()});setOrders(Array.isArray(r.data)?r.data:[])}catch{setError('We could not load your requests. Please try again.')}finally{setLoading(false)}}
 useEffect(()=>{load()},[])
 const summary=useMemo(()=>({total:orders.length,active:orders.filter(o=>!['Completed','Cancelled','Rejected'].includes(o.status)).length,completed:orders.filter(o=>o.status==='Completed').length}),[orders])
 if(loading)return <div className="dashboard-state"><div className="loading-dot"/><p>Loading your service requests...</p></div>
 if(error)return <div className="dashboard-state error-state"><h2>Something went wrong</h2><p>{error}</p><button onClick={load}>Try again</button></div>
 return <div className="client-dashboard">
  <section className="dashboard-hero"><div><span className="eyebrow">Client workspace</span><h1>My service requests</h1><p>Track every request from submission through completion.</p></div><Link className="btn btn-primary" to="/">Find a service</Link></section>
  <section className="dashboard-stat-grid"><div className="dashboard-stat"><span>Total</span><strong>{summary.total}</strong><small>Submitted requests</small></div><div className="dashboard-stat"><span>Active</span><strong>{summary.active}</strong><small>Being handled</small></div><div className="dashboard-stat"><span>Completed</span><strong>{summary.completed}</strong><small>Finished requests</small></div></section>
  <section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Request center</span><h2>Your requests</h2></div><Link className="text-link" to="/account-settings">Account settings →</Link></div>
   {orders.length===0?<div className="empty-dashboard"><div className="empty-icon">✓</div><h3>No requests yet</h3><p>Choose a service to start your first request.</p><Link className="btn btn-primary" to="/">Browse services</Link></div>:<div className="request-list">{orders.map(o=><article key={o.id} className="request-card">
    <div className="request-card-main"><div className="request-icon">P</div><div><div className="request-code">{o.order_code}</div><h3>{o.service}</h3><p>Submitted {new Date(o.created_at).toLocaleString()}</p></div></div>
    <div className="request-card-side"><span className={`status-pill status-${String(o.status||'').toLowerCase().replace(/\s+/g,'-')}`}>{o.status}</span><strong>₹{o.fee_inr}</strong></div>
    <div className="request-card-actions"><Link to={`/my-orders/${o.id}`}>View request</Link>{o.status==='Completed'&&<Link to={`/submit-review?order_id=${o.id}`}>Review</Link>}{!['Completed','Cancelled','Rejected'].includes(o.status)&&<Link to={`/submit-grievance?order_id=${o.id}`}>Get help</Link>}</div>
   </article>)}</div>}
  </section>
 </div>
}
