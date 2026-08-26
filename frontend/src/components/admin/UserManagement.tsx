import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchAdminUser, fetchAdminUsers, setClientActive } from '../../services/admin'

export default function UserManagement(){
  const [items,setItems] = useState<any[]>([])
  const [err,setErr] = useState('')
  const [loading,setLoading] = useState(true); const [q,setQ]=useState(''); const [page,setPage]=useState(1); const [meta,setMeta]=useState<any>({})
  const [selected,setSelected]=useState<any>(null)

  useEffect(()=>{
    let cancelled = false

    ;(async ()=>{
      try{
        setLoading(true)
        setErr('')
        const data = await fetchAdminUsers(page,q)
        if (!cancelled){setItems(Array.isArray(data.items) ? data.items : []);setMeta(data.meta||{})}
      }catch(e:any){
        if (!cancelled) setErr('Unable to load users. Please sign in again and refresh.')
      }finally{
        if (!cancelled) setLoading(false)
      }
    })()

    return () => { cancelled = true }
  },[page])

  return (
    <div>
      <h2>Registered clients</h2>
      <div className="admin-filters"><label>Search clients<input value={q} onChange={e=>setQ(e.target.value)} placeholder="Name, email or phone"/></label><button onClick={()=>{setPage(1);fetchAdminUsers(1,q).then(d=>{setItems(d.items||[]);setMeta(d.meta||{})}).catch(()=>setErr('Unable to load clients.'))}}>Search</button></div>
      {loading && <p className="info">Loading registered clients…</p>}
      {err && <p className="info" role="alert">{err}</p>}
      <div className="table-scroll" role="region" aria-label="Registered clients table" tabIndex={0}><table className="table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Requests</th><th>Status</th><th>Joined</th><th>Action</th></tr></thead>
        <tbody>
          {!loading && !err && items.length === 0 && (
            <tr><td colSpan={7}>No registered clients found.</td></tr>
          )}
          {items.map(u=> (
            <tr key={u.id}>
              <td>{u.name || '—'}</td>
              <td>{u.email || '—'}</td>
              <td>{u.phone || '—'}</td>
              <td>{u.request_count||0}</td>
              <td><span className={`status-pill ${u.is_active?'status-completed':'status-cancelled'}`}>{u.is_active?'Active':'Suspended'}</span></td>
              <td>{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
              <td><div className="button-row"><button className="btn-secondary" onClick={async()=>{try{setSelected(await fetchAdminUser(u.id))}catch{setErr('Unable to load this client.')}}}>View</button><button className={u.is_active?'btn-secondary':''} onClick={async()=>{try{await setClientActive(u.id,!u.is_active);setItems(current=>current.map(item=>item.id===u.id?{...item,is_active:!u.is_active}:item));if(selected?.user?.id===u.id)setSelected({...selected,user:{...selected.user,is_active:!u.is_active}})}catch{setErr('Unable to update this client account.')}}}>{u.is_active?'Suspend':'Reactivate'}</button></div></td>
            </tr>
          ))}
        </tbody>
      </table></div>
      {selected&&<section className="dashboard-section client-detail"><div className="section-header"><div><span className="eyebrow">Client record</span><h3>{selected.user.name}</h3><p>{selected.user.email} · {selected.user.phone||'No phone'} · {selected.user.is_active?'Active':'Suspended'}</p></div><button className="btn-secondary" onClick={()=>setSelected(null)}>Close</button></div><h4>Applications</h4>{selected.orders.length?<div className="card-list">{selected.orders.map((order:any)=><Link className="action-card" to={`/admin/orders/${order.id}`} key={order.id}><strong>{order.order_code} · {order.service}</strong><small>{order.status} · {new Date(order.created_at).toLocaleString()}</small></Link>)}</div>:<p>No applications submitted.</p>}</section>}
      <div className="pagination"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {meta.page||1} of {meta.pages||1}</span><button disabled={page>=(meta.pages||1)} onClick={()=>setPage(p=>p+1)}>Next</button></div>
    </div>
  )
}
