import React, { useEffect, useState } from 'react'
import { fetchAdminUsers } from '../../services/admin'

export default function UserManagement(){
  const [items,setItems] = useState<any[]>([])
  const [err,setErr] = useState('')
  const [loading,setLoading] = useState(true); const [q,setQ]=useState(''); const [page,setPage]=useState(1); const [meta,setMeta]=useState<any>({})

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
      <table className="table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Requests</th><th>Joined</th></tr></thead>
        <tbody>
          {!loading && !err && items.length === 0 && (
            <tr><td colSpan={5}>No registered clients found.</td></tr>
          )}
          {items.map(u=> (
            <tr key={u.id}>
              <td>{u.name || '—'}</td>
              <td>{u.email || '—'}</td>
              <td>{u.phone || '—'}</td>
              <td>{u.request_count||0}</td>
              <td>{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {meta.page||1} of {meta.pages||1}</span><button disabled={page>=(meta.pages||1)} onClick={()=>setPage(p=>p+1)}>Next</button></div>
    </div>
  )
}
