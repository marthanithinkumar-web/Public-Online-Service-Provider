import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {Link,useParams} from 'react-router-dom'
import {apiBase} from '../services/apiBase'
import {authHeader} from '../services/auth'

export default function OrderDetail(){
 const {id}=useParams();const [order,setOrder]=useState<any>(null);const [error,setError]=useState('');const [loading,setLoading]=useState(true)
 useEffect(()=>{if(!id)return;axios.get(`${apiBase}/orders/${id}`,{headers:authHeader()}).then(r=>setOrder(r.data)).catch(e=>setError(e?.response?.data?.error||'Unable to load this request.')).finally(()=>setLoading(false))},[id])
 if(loading)return <div className="dashboard-state"><div className="loading-dot"/><p>Loading request...</p></div>
 if(error||!order)return <div className="dashboard-state error-state"><h2>Request unavailable</h2><p>{error||'This request could not be found.'}</p><Link className="btn btn-primary" to="/my-orders">Back to requests</Link></div>
 const data=order.application_data||{}
 const terminal=['Completed','Cancelled','Rejected'].includes(order.status)
 return <div className="client-dashboard"><section className="dashboard-hero"><div><span className="eyebrow">Request {order.order_code}</span><h1>{order.service}</h1><p>Submitted {new Date(order.created_at).toLocaleString()}</p></div><span className={`status-pill status-${String(order.status||'').toLowerCase().replace(/\s+/g,'-')}`}>{order.status}</span></section>
  <section className="dashboard-section"><h2>Request progress</h2><div className="request-timeline"><div className="timeline-item active"><strong>Request submitted</strong><span>{new Date(order.created_at).toLocaleString()}</span></div><div className="timeline-item"><strong>Current status</strong><span>{order.status}</span></div></div></section>
  <section className="dashboard-section"><h2>Application information</h2><div className="request-summary">{Object.entries(data).filter(([k])=>k!=='service_name').map(([k,v])=><p key={k}><strong>{k.replace(/_/g,' ')}:</strong> {String(v||'—')}</p>)}</div></section>
  <section className="dashboard-section"><h2>Request actions</h2><p>{terminal?'This request is closed.':'If the provider needs more information, the request status will show Documents Required.'}</p><div className="cta-row">{!terminal&&<Link className="btn btn-secondary" to={`/submit-grievance?order_id=${order.id}`}>Get help</Link>}{order.status==='Completed'&&<Link className="btn btn-primary" to={`/submit-review?order_id=${order.id}`}>Leave a review</Link>}<Link className="btn btn-secondary" to="/my-orders">Back to requests</Link></div></section>
 </div>
}
