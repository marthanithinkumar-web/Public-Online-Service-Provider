import React, {useEffect, useMemo, useState} from 'react'
import {Link} from 'react-router-dom'
import axios from 'axios'
import {authHeader, fetchClientProfile} from '../services/auth'
import {apiBase} from '../services/apiBase'
import SearchPanel from '../components/ui/SearchPanel'
import CategoriesSection from '../components/ui/CategoriesSection'
import ClientWorkspaceNav from '../components/ui/ClientWorkspaceNav'

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
    setNotificationError('')
    const [ordersResult,notificationsResult,profileResult]=await Promise.allSettled([
        axios.get(`${apiBase}/orders/mine`,{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS}),
        axios.get(`${apiBase}/notifications`,{headers:authHeader(),timeout:REQUEST_TIMEOUT_MS}),
        fetchClientProfile(),
    ])
    if(ordersResult.status==='fulfilled')setOrders(Array.isArray(ordersResult.value.data)?ordersResult.value.data:[])
    else{const err:any=ordersResult.reason;setError(axios.isCancel(err)?'The request was cancelled. Please try again.':err?.code==='ECONNABORTED'?'Your applications took too long to load. You can still search services below, or try loading the dashboard again.':'We could not load your applications. You can still search services below, or try again.')}
    if(notificationsResult.status==='fulfilled'){const data=notificationsResult.value.data;setNotifications(data.items||[]);setUnread(data.unread||0)}
    else setNotificationError('Notifications are temporarily unavailable. Your service search and applications remain usable.')
    if(profileResult.status==='fulfilled')setProfile(profileResult.value.user||null)
    setLoading(false)
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

  return <div className="client-workspace-shell"><ClientWorkspaceNav/><div className="client-dashboard">
    <section className="dashboard-hero"><div><span className="eyebrow">Client dashboard</span><h1>Welcome{profile?.name?`, ${profile.name}`:''}</h1><p>Find services, track active applications, and review important updates in one place.</p></div><div className="button-row"><a className="btn btn-primary" href="#service-search">Find a service</a><Link className="btn btn-secondary" to="/account-settings">My profile</Link></div></section>
    <SearchPanel context="dashboard"/>
    {loading&&<div className="dashboard-state" role="status"><div className="loading-dot"/><p>Loading your applications and updates… Service search is ready to use above.</p></div>}
    {error&&<div className="dashboard-state error-state" role="alert"><h2>Applications could not be loaded</h2><p>{error}</p><button onClick={load}>Try loading applications again</button></div>}
    {!loading&&!error&&<>
    <section className="dashboard-stat-grid"><div className="dashboard-stat"><span>Total applications</span><strong>{summary.total}</strong><small>Submitted requests</small></div><div className="dashboard-stat"><span>Active applications</span><strong>{summary.active}</strong><small>Being handled</small></div><div className="dashboard-stat"><span>Notifications</span><strong>{unread}</strong><small>Unread updates</small></div></section>
    <section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Quick actions</span><h2>What would you like to do?</h2></div></div><div className="dashboard-action-grid"><a className="action-card" href="#service-search"><strong>Search services</strong><small>Find application assistance</small></a><a className="action-card" href="#applications"><strong>Track applications</strong><small>Review status and next steps</small></a><Link className="action-card" to="/submit-grievance"><strong>Get help</strong><small>Raise a request-related grievance</small></Link><Link className="action-card" to="/account-settings"><strong>Manage profile</strong><small>Update account and security</small></Link></div></section>
    <CategoriesSection/>
    {recentServices.length>0&&<section className="dashboard-section"><div className="section-header inline"><div><span className="eyebrow">Recently used</span><h2>Your services</h2></div></div><div className="dashboard-action-grid">{recentServices.map((order:any)=><Link className="action-card" to={`/service/${order.service_id}`} key={order.service_id}><strong>{order.service}</strong><small>Start another application</small></Link>)}</div></section>}
    {notificationError&&<p className="info" role="alert">{notificationError}</p>}
    {notifications.length>0&&<section className="dashboard-section" id="notifications"><div className="section-header inline"><div><span className="eyebrow">Updates</span><h2>Recent notifications</h2></div>{unread>0&&<button disabled={markingRead} onClick={markAllRead}>{markingRead?'Updating…':'Mark all read'}</button>}</div><div className="notification-list">{notifications.slice(0,5).map(item=><article key={item.id} className={item.is_read?'notification-card':'notification-card unread'}><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small>{item.order_id&&<Link to={`/my-orders/${item.order_id}`}>View application</Link>}</article>)}</div></section>}
    <section className="dashboard-section" id="applications"><div className="section-header inline"><div><span className="eyebrow">My applications</span><h2>Application history</h2></div><Link className="text-link" to="/account-settings">Account settings →</Link></div>
      <div className="application-toolbar"><label>Search applications<input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Application ID or service"/></label><div className="filter-tabs" role="group" aria-label="Filter applications">{FILTERS.map(item=><button type="button" className={filter===item?'active':''} aria-pressed={filter===item} onClick={()=>setFilter(item)} key={item}>{item}</button>)}</div></div>
      {orders.length===0?<div className="empty-dashboard"><div className="empty-icon">✓</div><h3>No applications yet</h3><p>Choose a service to start your first application.</p><a className="btn btn-primary" href="#service-search">Browse services</a></div>:filteredOrders.length===0?<div className="empty-dashboard"><h3>No matching applications</h3><p>Try another status or search term.</p></div>:<div className="request-list">{filteredOrders.map(order=><article key={order.id} className="request-card"><div className="request-card-main"><div className="request-icon">P</div><div><div className="request-code">{order.order_code}</div><h3>{order.service}</h3><p>Submitted {new Date(order.created_at).toLocaleString()} · Last updated {new Date(order.updated_at||order.created_at).toLocaleString()}</p></div></div><div className="request-card-side"><span className={`status-pill status-${String(order.status||'').toLowerCase().replace(/\s+/g,'-')}`}>{order.status}</span><span className="request-fee-mini"><strong>Assistance ₹{order.fee_inr}</strong><small>Official: {order.official_fee_status==='unconfirmed'?'To be confirmed':`₹${order.official_fee_inr||0}`}</small></span></div><div className="request-card-actions"><Link to={`/my-orders/${order.id}`}>View application & fee summary</Link>{order.status==='Completed'&&<Link to={`/submit-review?order_id=${order.id}`}>Review</Link>}{!CLOSED.includes(order.status)&&<Link to={`/submit-grievance?order_id=${order.id}`}>Get help</Link>}</div></article>)}</div>}
    </section>
    </>}
  </div></div>
}
