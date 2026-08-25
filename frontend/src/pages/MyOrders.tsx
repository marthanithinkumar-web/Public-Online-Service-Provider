import React, {useEffect, useMemo, useState} from 'react'
import {Link} from 'react-router-dom'
import axios from 'axios'
import {authHeader, fetchClientProfile} from '../services/auth'
import {apiBase} from '../services/apiBase'
import SearchPanel from '../components/ui/SearchPanel'
import CategoriesSection from '../components/ui/CategoriesSection'

const REQUEST_TIMEOUT_MS = 15000
const CLOSED = ['Completed','Cancelled','Rejected']
const FILTERS = ['All','Pending','Under Review','In Progress','Completed','Rejected']

export default function MyOrders(){
  const [orders,setOrders]=useState<any[]>([])
  const [notifications,setNotifications]=useState<any[]>([])
  const [unread,setUnread]=useState(0)
  const [profile,setProfile]=useState<any>(null)
  const [filter,setFilter]=useState('All')
  const [query,setQuery]=useState('')
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [notificationError,setNotificationError]=useState('');const [markingRead,setMarkingRead]=useState(false)

  const markAllRead=async()=>{if(markingRead)return;setMarkingRead(true);setNotificationError('');try{await axios.post(`${apiBase}/notifications/read-all`,{}, {headers:authHeader(),timeout:REQUEST_TIMEOUT_MS});setUnread(0);setNotifications(items=>items.map(item=>({...item,is_read:true})))}catch{setNotificationError('Unable to mark notifications as read. Please try again.')}finally{setMarkingRead(false)}}

  const load=async()=>{
    setLoading(true);setError('')
    try{
      const [r,n,p]=await Promise.all([
        axios.get(`${apiBase}/orders/mine`,{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS}),
        axios.get(`${apiBase}/notifications`,{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS}),
        fetchClientProfile(),
      ])
      setOrders(Array.isArray(r.data)?r.data:[])
      setNotifications(n.data.items||[]);setUnread(n.data.unread||0);setProfile(p.user||null)
    }catch(err:any){
      setError(axios.isCancel(err)?'The request was cancelled. Please try again.':err?.code==='ECONNABORTED'?'The server took too long to respond. Please try again.':'We could not load your dashboard. Please try again.')
    }finally{setLoading(false)}
  }

  useEffect(()=>{load()},[])
  const summary=useMemo(()=>({total:orders.length,active:orders.filter(o=>!CLOSED.includes(o.status)).length}),[orders])
  const recentServices=useMemo(()=>Array.from(new Map(orders.filter(o=>o.service_id).map(o=>[o.service_id,o])).values()).slice(0,4),[orders])
  const filteredOrders=useMemo(()=>orders.filter(order=>{
    const statusMatches=filter==='All'||(filter==='Pending'?['New','Submitted','Pending','Documents Required'].includes(order.status):order.status===filter)
    const term=query.trim().toLowerCase()
    const searchMatches=!term||`${order.order_code} ${order.service}`.toLowerCase().includes(term)
    return statusMatches&&searchMatches
  }),[orders,filter,query])

  if(loading)return <div className="dashboard-state"><div className="loading-dot"/><p>Loading your service dashboard...</p></div>
  if(error)return <div className="dashboard-state error-state"><h2>Something went wrong</h2><p>{error}</p><button onClick={load}>Try again</button></div>

  return <div className="client-dashboard">
    <section className="dashboard-hero"><div><span className="eyebrow">Client dashboard</span><h1>Welcome{profile?.name?`, ${profile.name}`:''}</h1><p>Find services, track active applications, and review important updates in one place.</p></div><div className="button-row"><Link className="btn btn-primary" to="/#service-search">Find a service</Link><Link className="btn btn-secondary" to="/account-settings">My profile</Link></div></section>
    <section className="dashboard-stat-grid"><div className="dashboard-stat"><span>Total applications</span><strong>{summary.total}</strong><small>Submitted requests</small></div><div className="dashboard-stat"><span>Active applications</span><strong>{summary.active}</strong><small>Being handled</small></div><div className="dashboard-stat"><span>Notifications</span><strong>{unread}</strong><small>Unread updates</small></div></section>
    <section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Quick actions</span><h2>What would you like to do?</h2></div></div><div className="dashboard-action-grid"><Link className="action-card" to="/#service-search"><strong>Search services</strong><small>Find application assistance</small></Link><a className="action-card" href="#applications"><strong>Track applications</strong><small>Review status and next steps</small></a><Link className="action-card" to="/submit-grievance"><strong>Get help</strong><small>Raise a request-related grievance</small></Link><Link className="action-card" to="/account-settings"><strong>Manage profile</strong><small>Update account and security</small></Link></div></section>
    <SearchPanel/><CategoriesSection/>
    {recentServices.length>0&&<section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Recently used</span><h2>Your services</h2></div></div><div className="dashboard-action-grid">{recentServices.map((order:any)=><Link className="action-card" to={`/service/${order.service_id}`} key={order.service_id}><strong>{order.service}</strong><small>Start another application</small></Link>)}</div></section>}
    {notifications.length>0&&<section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Updates</span><h2>Recent notifications</h2></div>{unread>0&&<button disabled={markingRead} onClick={markAllRead}>{markingRead?'Updating…':'Mark all read'}</button>}</div>{notificationError&&<p className="info" role="alert">{notificationError}</p>}<div className="notification-list">{notifications.slice(0,5).map(item=><article key={item.id} className={item.is_read?'notification-card':'notification-card unread'}><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small>{item.order_id&&<Link to={`/my-orders/${item.order_id}`}>View application</Link>}</article>)}</div></section>}
    <section className="dashboard-section" id="applications"><div className="section-header inline"><div><span className="eyebrow">My applications</span><h2>Application history</h2></div><Link className="text-link" to="/account-settings">Account settings →</Link></div>
      <div className="application-toolbar"><label>Search applications<input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Application ID or service"/></label><div className="filter-tabs" role="group" aria-label="Filter applications">{FILTERS.map(item=><button type="button" className={filter===item?'active':''} aria-pressed={filter===item} onClick={()=>setFilter(item)} key={item}>{item}</button>)}</div></div>
      {orders.length===0?<div className="empty-dashboard"><div className="empty-icon">✓</div><h3>No applications yet</h3><p>Choose a service to start your first application.</p><Link className="btn btn-primary" to="/#service-search">Browse services</Link></div>:filteredOrders.length===0?<div className="empty-dashboard"><h3>No matching applications</h3><p>Try another status or search term.</p></div>:<div className="request-list">{filteredOrders.map(order=><article key={order.id} className="request-card"><div className="request-card-main"><div className="request-icon">P</div><div><div className="request-code">{order.order_code}</div><h3>{order.service}</h3><p>Submitted {new Date(order.created_at).toLocaleString()} · Last updated {new Date(order.updated_at||order.created_at).toLocaleString()}</p></div></div><div className="request-card-side"><span className={`status-pill status-${String(order.status||'').toLowerCase().replace(/\s+/g,'-')}`}>{order.status}</span><span className="request-fee-mini"><strong>Assistance ₹{order.fee_inr}</strong><small>Official: {order.official_fee_status==='unconfirmed'?'To be confirmed':`₹${order.official_fee_inr||0}`}</small></span></div><div className="request-card-actions"><Link to={`/my-orders/${order.id}`}>View application & fee summary</Link>{order.status==='Completed'&&<Link to={`/submit-review?order_id=${order.id}`}>Review</Link>}{!CLOSED.includes(order.status)&&<Link to={`/submit-grievance?order_id=${order.id}`}>Get help</Link>}</div></article>)}</div>}
    </section>
  </div>
}
