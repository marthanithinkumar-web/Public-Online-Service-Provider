import React, { useEffect, useMemo, useState } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import { authHeader } from '../services/auth'
import { apiBase } from '../services/apiBase'

export default function MyOrders(){
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(()=>{
    const load = async ()=>{
      try{
        const res = await axios.get(`${apiBase}/orders/mine`, { headers: authHeader() })
        setOrders(Array.isArray(res.data) ? res.data : [])
      }catch(err){ setError('We could not load your requests. Please try again.') }
      finally{ setLoading(false) }
    }
    load()
  }, [])

  const summary = useMemo(() => ({
    total: orders.length,
    active: orders.filter(o => !['Completed','Cancelled'].includes(o.status)).length,
    completed: orders.filter(o => o.status === 'Completed').length,
  }), [orders])

  if(loading) return <div className="dashboard-state"><div className="loading-dot"/><p>Loading your service requests...</p></div>
  if(error) return <div className="dashboard-state error-state"><h2>Something went wrong</h2><p>{error}</p><button onClick={()=>window.location.reload()}>Try again</button></div>

  return (
    <div className="client-dashboard">
      <section className="dashboard-hero">
        <div><span className="eyebrow">Citizen workspace</span><h1>My service requests</h1><p>Track applications, see progress updates, and get help whenever you need it.</p></div>
        <Link className="btn btn-primary" to="/">Find a service</Link>
      </section>

      <section className="dashboard-stat-grid" aria-label="Request summary">
        <div className="dashboard-stat"><span>Total requests</span><strong>{summary.total}</strong><small>All submitted services</small></div>
        <div className="dashboard-stat"><span>Active</span><strong>{summary.active}</strong><small>Currently being handled</small></div>
        <div className="dashboard-stat"><span>Completed</span><strong>{summary.completed}</strong><small>Successfully finished</small></div>
      </section>

      <section className="dashboard-section">
        <div className="section-header inline"><div><span className="eyebrow">Activity</span><h2>Recent requests</h2></div><Link className="text-link" to="/account-settings">Account settings →</Link></div>
        {orders.length === 0 ? (
          <div className="empty-dashboard"><div className="empty-icon">✓</div><h3>No requests yet</h3><p>Choose a public service to start your first request.</p><Link className="btn btn-primary" to="/">Browse services</Link></div>
        ) : (
          <div className="request-list">{orders.map(o=>(
            <article key={o.id} className="request-card">
              <div className="request-card-main"><div className="request-icon">P</div><div><div className="request-code">{o.order_code}</div><h3>{o.service}</h3><p>Submitted {new Date(o.created_at).toLocaleString()}</p></div></div>
              <div className="request-card-side"><span className={`status-pill status-${String(o.status || '').toLowerCase().replace(/\s+/g,'-')}`}>{o.status}</span><strong>₹{o.fee_inr}</strong></div>
              <div className="request-card-actions"><Link to="/submit-grievance">Need help?</Link><Link to="/submit-review">Leave a review</Link></div>
            </article>
          ))}</div>
        )}
      </section>
    </div>
  )
}
