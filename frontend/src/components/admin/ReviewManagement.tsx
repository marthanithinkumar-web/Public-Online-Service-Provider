import React, { useEffect, useState } from 'react'
import { fetchReviews, publishReview } from '../../services/admin'

export default function ReviewManagement(){
  const [items, setItems] = useState<any[]>([])
  const [meta, setMeta] = useState<any>({})
  const [page, setPage] = useState(1)

  const load = async (p=1)=>{
    try{
      const res = await fetchReviews(p,20)
      setItems(res.items || [])
      setMeta(res.meta || {})
    }catch(err){ console.error(err) }
  }
  useEffect(()=>{ load(page) }, [page])

  const toggle = async (id:number, current:boolean)=>{
    try{
      await publishReview(id, !current)
      load(page)
    }catch(err){ console.error(err) }
  }

  return (
    <div>
      <h2>Reviews</h2>
      <ul>
        {items.map(r=> (
          <li key={r.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div>Rating: {r.rating} — {r.comment}</div>
            <div>Public: {String(r.is_public)}</div>
            <div><button onClick={()=>toggle(r.id, r.is_public)}>{r.is_public ? 'Hide' : 'Make public'}</button></div>
          </li>
        ))}
      </ul>
      <div style={{display:'flex',gap:8}}>
        <button onClick={()=>setPage(Math.max(1,page-1))}>Prev</button>
        <div>Page {meta.page ?? 1} / {meta.pages ?? 1}</div>
        <button onClick={()=>setPage((meta.page||1)+1)}>Next</button>
      </div>
    </div>
  )
}
