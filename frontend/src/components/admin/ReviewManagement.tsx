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
    <div>
      <h2>Reviews</h2>
      {error&&<div className="dashboard-state error-state"><p>{error}</p><button onClick={()=>load(page)}>Try again</button></div>}
      {loading?<div className="dashboard-state"><div className="loading-dot"/><p>Loading reviews...</p></div>:!items.length&&!error?<div className="dashboard-state"><p>No reviews found.</p></div>:<ul>
        {items.map(r=> (
          <li key={r.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div>Rating: {r.rating} — {r.comment}</div>
            <div>Public: {String(r.is_public)}</div>
            <div><button disabled={busyId===r.id} onClick={()=>toggle(r.id, r.is_public)}>{busyId===r.id?'Updating…':r.is_public ? 'Hide' : 'Make public'}</button></div>
          </li>
        ))}
      </ul>}
      <div style={{display:'flex',gap:8}}>
        <button disabled={loading||page<=1} onClick={()=>setPage(Math.max(1,page-1))}>Prev</button>
        <div>Page {meta.page ?? 1} / {meta.pages ?? 1}</div>
        <button disabled={loading||page>=(meta.pages||1)} onClick={()=>setPage((meta.page||1)+1)}>Next</button>
      </div>
    </div>
  )
}
