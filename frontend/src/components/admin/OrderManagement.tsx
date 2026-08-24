import React,{useEffect,useState} from 'react'
import {Link,useSearchParams} from 'react-router-dom'
import {fetchAdminOrders} from '../../services/admin'

const STATUSES=['','New','Under Review','Documents Required','In Progress','Completed','Rejected','Cancelled']

export default function OrderManagement(){
 const [params,setParams]=useSearchParams();const status=params.get('status')||''
 const [orders,setOrders]=useState<any[]>([]);const [meta,setMeta]=useState<any>({});const [page,setPage]=useState(1);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [q,setQ]=useState('');const [dateFrom,setDateFrom]=useState('');const [dateTo,setDateTo]=useState('')
 const load=async(p=1)=>{setLoading(true);setError('');try{const res=await fetchAdminOrders(p,20,status,q,dateFrom,dateTo);setOrders(res.items||[]);setMeta(res.meta||{})}catch(err:any){setError(err?.response?.data?.error||'Unable to load requests. Please try again.')}finally{setLoading(false)}}
 useEffect(()=>{setPage(1)},[status])
 useEffect(()=>{load(page)},[page,status])
 return <div className="admin-orders"><div className="section-header"><div><span className="eyebrow">Request queue</span><h2>{status||'All requests'}</h2><p>Open a request to process its application, documents, timeline and status.</p></div></div>
  <div className="admin-filters"><label>Search<input value={q} onChange={e=>setQ(e.target.value)} placeholder="Request ID, client, phone or service"/></label><label>Status<select value={status} onChange={e=>{const next=e.target.value;if(next)params.set('status',next);else params.delete('status');setParams(params)}}>{STATUSES.map(s=><option key={s} value={s}>{s||'All statuses'}</option>)}</select></label><label>From<input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)}/></label><label>To<input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)}/></label><button onClick={()=>{setPage(1);load(1)}}>Apply filters</button></div>
  {error&&<div className="dashboard-state error-state"><p>{error}</p><button onClick={()=>load(page)}>Try again</button></div>}
  {loading?<div className="dashboard-state"><div className="loading-dot"/><p>Loading requests...</p></div>:!orders.length&&!error?<div className="dashboard-state"><p>No requests found for this filter.</p></div>:<ul>{orders.map(o=><li key={o.id} style={{border:'1px solid #eee',padding:12,margin:'8px 0',borderRadius:8}}><div><strong>{o.order_code}</strong> — {o.service}</div><div>{o.client_name} • {o.phone}</div><div>Status: {o.status}</div><div>Fee: ₹{o.fee_inr}</div><Link className="btn btn-secondary" to={`/admin/orders/${o.id}`}>Open request</Link></li>)}</ul>}
  <div style={{display:'flex',gap:8,alignItems:'center'}}><button disabled={loading||page<=1} onClick={()=>setPage(p=>Math.max(1,p-1))}>Prev</button><div>Page {meta.page??page} / {meta.pages??1}</div><button disabled={loading||page>=(meta.pages??1)} onClick={()=>setPage(p=>p+1)}>Next</button></div>
 </div>
}
