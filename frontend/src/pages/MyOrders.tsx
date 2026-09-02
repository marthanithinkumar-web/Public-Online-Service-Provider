import React, {useEffect, useMemo, useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import axios from 'axios'
import {authHeader, fetchClientProfile} from '../services/auth'
import {apiBase} from '../services/apiBase'
import {applicationName,applicationSearchText} from '../services/applicationLabel'
import SearchPanel from '../components/ui/SearchPanel'
import CategoriesSection from '../components/ui/CategoriesSection'
import ClientWorkspaceNav from '../components/ui/ClientWorkspaceNav'
import RequestFeedback from '../components/ui/RequestFeedback'
import JobRecommendations from '../components/jobs/JobRecommendations'

const REQUEST_TIMEOUT_MS = 15000
const CLOSED = ['Completed','Cancelled','Rejected']
const FILTERS = ['All','Pending','Under Review','In Progress','Completed','Rejected']

export default function MyOrders(){
  const location=useLocation()
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
  const filteredOrders=useMemo(()=>orders.filter(order=>{
    const statusMatches=filter==='All'||(filter==='Pending'?['New','Submitted','Pending','Documents Required'].includes(order.status):order.status===filter)
    const term=query.trim().toLowerCase()
    const searchMatches=!term||applicationSearchText(order).includes(term)
    return statusMatches&&searchMatches
  }),[orders,filter,query])

  const view=location.hash.replace('#','')
  const applications=<section className="dashboard-section" id="applications"><div className="section-header inline"><div><h2>{view==='track'?'Track My Request':'My Service Applications'}</h2></div></div>
    <div className="application-toolbar"><label>Search applications<input value={query} onChange={event=>setQuery(event.target.value)} placeholder="Order number, service or job title"/></label><div className="filter-tabs" role="group" aria-label="Filter applications">{FILTERS.map(item=><button type="button" className={filter===item?'active':''} aria-pressed={filter===item} onClick={()=>setFilter(item)} key={item}>{item}</button>)}</div></div>
    {orders.length===0?<div className="empty-dashboard"><h3>No applications yet</h3></div>:filteredOrders.length===0?<div className="empty-dashboard"><h3>No matching applications</h3></div>:<div className="request-list">{filteredOrders.map(order=><article key={order.id} className="request-card"><div className="request-card-main"><div className="request-icon">A</div><div><div className="request-code">{order.order_code}</div><h3>{applicationName(order)}</h3>{applicationName(order)!==order.service&&<p>{order.service}</p>}<p>{new Date(order.created_at).toLocaleString()}</p></div></div><div className="request-card-side"><span className={`status-pill status-${String(order.status||'').toLowerCase().replace(/\s+/g,'-')}`}>{order.status}</span><span className="request-fee-mini"><strong>Applicable Assistance Fee ₹{order.fee_inr}</strong><small>Official fee: {order.official_fee_status==='unconfirmed'?'To be confirmed':`₹${order.official_fee_inr||0}`}</small></span></div><div className="request-card-actions"><Link to={`/my-orders/${order.id}`}>View application</Link>{!CLOSED.includes(order.status)&&<Link to={`/submit-grievance?order_id=${order.id}`}>Get help</Link>}</div></article>)}</div>}
  </section>
  const notificationSection=<>{notificationError&&<p className="info" role="alert">{notificationError}</p>}{notifications.length?<section className="dashboard-section" id="notifications"><div className="section-header inline"><h2>Notifications</h2>{unread>0&&<button disabled={markingRead} onClick={markAllRead}>{markingRead?'Updating…':'Mark all read'}</button>}</div><div className="notification-list">{notifications.map(item=><article key={item.id} className={item.is_read?'notification-card':'notification-card unread'}><strong>{item.title}</strong><p>{item.message}</p><small>{new Date(item.created_at).toLocaleString()}</small>{item.order_id&&<Link to={`/my-orders/${item.order_id}`}>View application</Link>}</article>)}</div></section>:<section className="dashboard-section"><h2>Notifications</h2><p>No notifications.</p></section>}</>

  return <div className="client-workspace-shell"><ClientWorkspaceNav/><div className="client-dashboard">
    <section className="dashboard-hero"><div><span className="eyebrow">Client dashboard</span><h1>{view==='applications'?'My Applications':view==='track'?'Track My Request':view==='service-search'?'Find Services':view==='notifications'?'Notifications':`Welcome${profile?.name?`, ${profile.name}`:''}`}</h1><p>{view?'Your secure account workspace.':'Here are your official-source opportunities and service application updates.'}</p></div><span className="dashboard-safety">✓ OTP, PIN and passwords are never requested</span></section>
    {loading&&<div className="dashboard-state" role="status"><div className="loading-dot"/><p>Loading…</p></div>}
    {error&&<div className="dashboard-state error-state" role="alert"><h2>Applications could not be loaded</h2><p>{error}</p><button onClick={load}>Try loading applications again</button></div>}
    {!loading&&!error&&<>
    {(view==='applications'||view==='track')&&applications}
    {view==='service-search'&&<><SearchPanel context="dashboard"/><CategoriesSection/></>}
    {view==='notifications'&&notificationSection}
    {!view&&<><section className="dashboard-stat-grid"><div className="dashboard-stat"><span>Applications</span><strong>{summary.total}</strong></div><div className="dashboard-stat"><span>Active</span><strong>{summary.active}</strong></div><div className="dashboard-stat"><span>Unread</span><strong>{unread}</strong></div></section><JobRecommendations profile={profile}/><section className="dashboard-section"><div className="dashboard-action-grid"><Link className="action-card" to="/my-orders#service-search"><strong>Find Services</strong><small>Search all available assistance</small></Link><Link className="action-card" to="/my-orders#applications"><strong>My Applications</strong><small>Review status and next steps</small></Link><Link className="action-card" to="/grievances"><strong>Help & Grievances</strong><small>Contact the service administrator</small></Link></div></section>{orders.length>0&&applications}{orders.length>0&&<section className="dashboard-section" id="feedback"><RequestFeedback orders={orders}/></section>}</>}
    </>}
  </div></div>
}
