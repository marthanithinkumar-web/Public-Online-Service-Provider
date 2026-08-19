import React, { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchAdminOrders } from '../../services/admin'

export default function AdminDashboard(){
  const [meta, setMeta] = useState<any>({})
  const [counts, setCounts] = useState<any>({})
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    const load = async ()=>{
      try{
        const totalRes = await fetchAdminOrders(1,1,'')
        setMeta(totalRes.meta || {})
        const statuses = ['New','Contacted','In Progress','Completed']
        const c:any = {}
        for(const s of statuses){
          const r = await fetchAdminOrders(1,1,s)
          c[s] = r.meta ? r.meta.total : 0
        }
        setCounts(c)
      }catch(err){
        console.error(err)
      }finally{
        setLoading(false)
      }
    }
    load()
  }, [])

  const active = useMemo(() => (counts['New'] || 0) + (counts['Contacted'] || 0) + (counts['In Progress'] || 0), [counts])

  if(loading) return <div className="dashboard-state"><div className="loading-dot"/><p>Loading admin overview...</p></div>

  return (
    <div className="admin-dashboard">
      <div className="dashboard-welcome">
        <div><span className="eyebrow">Operations overview</span><h2>Good morning, Admin</h2><p>Keep citizen requests moving and resolve important issues from one workspace.</p></div>
        <Link className="btn btn-primary" to="/admin/orders">Review requests</Link>
      </div>

      <div className="dashboard-stat-grid admin-stats">
        <div className="dashboard-stat"><span>Total requests</span><strong>{meta.total ?? 0}</strong><small>All citizen requests</small></div>
        <div className="dashboard-stat"><span>Active work</span><strong>{active}</strong><small>Needs attention</small></div>
        <div className="dashboard-stat"><span>New</span><strong>{counts['New'] ?? 0}</strong><small>Recently submitted</small></div>
        <div className="dashboard-stat"><span>Completed</span><strong>{counts['Completed'] ?? 0}</strong><small>Successfully delivered</small></div>
      </div>

      <div className="admin-dashboard-grid">
        <section className="dashboard-section">
          <div className="section-header inline"><div><span className="eyebrow">Work queue</span><h2>Request pipeline</h2></div></div>
          <div className="pipeline-list">
            {[
              ['New', counts['New'] ?? 0, 'Review newly submitted requests', '/admin/orders'],
              ['Contacted', counts['Contacted'] ?? 0, 'Follow up with citizens', '/admin/orders'],
              ['In Progress', counts['In Progress'] ?? 0, 'Requests currently being handled', '/admin/orders'],
              ['Completed', counts['Completed'] ?? 0, 'Recently completed services', '/admin/orders'],
            ].map(([label, count, hint, href]) => (
              <Link className="pipeline-row" key={String(label)} to={String(href)}>
                <span className="pipeline-label"><strong>{label}</strong><small>{hint}</small></span>
                <span className="pipeline-count">{count}</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="dashboard-section quick-actions">
          <div className="section-header inline"><div><span className="eyebrow">Shortcuts</span><h2>Quick actions</h2></div></div>
          <Link to="/admin/orders" className="action-card"><span>Requests</span><small>Review and update citizen requests →</small></Link>
          <Link to="/admin/services" className="action-card"><span>Services</span><small>Manage your public service catalogue →</small></Link>
          <Link to="/admin/grievances" className="action-card"><span>Grievances</span><small>Respond to citizen concerns →</small></Link>
          <Link to="/admin/reviews" className="action-card"><span>Reviews</span><small>Monitor feedback and trust signals →</small></Link>
        </section>
      </div>
    </div>
  )
}
