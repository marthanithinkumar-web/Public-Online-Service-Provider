import React, { useEffect, useState } from 'react'
import { fetchGrievances, updateGrievanceStatus } from '../../services/admin'

export default function GrievanceManagement(){
  const [items, setItems] = useState<any[]>([])
  const [meta, setMeta] = useState<any>({})
  const [page, setPage] = useState(1)

  const load = async (p=1)=>{
    try{
      const res = await fetchGrievances(p,20)
      setItems(res.items || [])
      setMeta(res.meta || {})
    }catch(err){ console.error(err) }
  }
  useEffect(()=>{ load(page) }, [page])

  const change = async (id:number)=>{
    const s = prompt('New status (New, Under Review, Resolved, Closed)')
    if(!s) return
    try{
      await updateGrievanceStatus(id, s)
      load(page)
    }catch(err){ console.error(err) }
  }

  return (
    <div>
      <h2>Grievances</h2>
      <ul>
        {items.map(g=> (
          <li key={g.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div><strong>{g.grievance_code}</strong> — {g.client_name}</div>
            <div>{g.description}</div>
            <div>Status: {g.status}</div>
            <div><button onClick={()=>change(g.id)}>Change status</button></div>
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
