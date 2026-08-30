import React, { useEffect, useState } from 'react'
import { fetchReviews, publishReview } from '../../services/admin'

export default function ReviewManagement(){
  const [items, setItems] = useState<any[]>([])
  const [meta, setMeta] = useState<any>({})
  const [page, setPage] = useState(1)
  const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [busyId,setBusyId]=useState<number|null>(null)

  const load = async (p=1)=>{
    try{setLoading(true);setError('')
      const res = await fetchReviews(p,20)
      setItems(res.items || [])
      setMeta(res.meta || {})
    }catch{ setError('Unable to load reviews. Please try again.') }finally{setLoading(false)}
  }
  useEffect(()=>{ load(page) }, [page])

  const toggle = async (id:number, current:boolean)=>{
    try{setBusyId(id);setError('')
      await publishReview(id, !current)
      load(page)
    }catch{ setError('Unable to update review visibility.') }finally{setBusyId(null)}
  }

  return (
    <div className="admin-record-page">
      <div className="section-header"><div><span className="eyebrow">Client feedback</span><h2>Ratings & suggestions</h2></div></div>
      {error&&<div className="dashboard-state error-state"><p>{error}</p><button onClick={()=>load(page)}>Try again</button></div>}
      {loading?<div className="dashboard-state"><div className="loading-dot"/><p>Loading reviews...</p></div>:!items.length&&!error?<div className="dashboard-state"><p>No reviews found.</p></div>:<ul className="admin-record-list stacked">
        {items.map(r=> (
          <li key={r.id}>
            <div><strong>{r.rating}/5 ★</strong>{r.comment&&<p>{r.comment}</p>}<small>{r.client_name||'Client'} · {r.service||'Service'} · {r.order_code||'Request'} · {new Date(r.created_at).toLocaleString()}</small></div>
            <div>{r.is_public?'Shown on homepage':'Private'}</div>
            <div><button disabled={busyId===r.id} onClick={()=>toggle(r.id, r.is_public)}>{busyId===r.id?'Updating…':r.is_public ? 'Hide' : 'Make public'}</button></div>
          </li>
        ))}
      </ul>}
      <div className="pagination">
        <button disabled={loading||page<=1} onClick={()=>setPage(Math.max(1,page-1))}>Prev</button>
        <span>Page {meta.page ?? 1} of {meta.pages ?? 1}</span>
        <button disabled={loading||page>=(meta.pages||1)} onClick={()=>setPage((meta.page||1)+1)}>Next</button>
      </div>
    </div>
  )
}
