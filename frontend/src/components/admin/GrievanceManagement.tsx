import React, { useEffect, useState } from 'react'
import { fetchGrievances, updateGrievanceStatus } from '../../services/admin'

export default function GrievanceManagement(){
  const [items, setItems] = useState<any[]>([])
  const [meta, setMeta] = useState<any>({})
  const [page, setPage] = useState(1)
  const [loading,setLoading]=useState(true);const [error,setError]=useState('');const [busyId,setBusyId]=useState<number|null>(null);const [nextStatus,setNextStatus]=useState<Record<number,string>>({})

  const load = async (p=1)=>{
    try{setLoading(true);setError('')
      const res = await fetchGrievances(p,20)
      setItems(res.items || [])
      setMeta(res.meta || {})
    }catch{ setError('Unable to load grievances. Please try again.') }finally{setLoading(false)}
  }
  useEffect(()=>{ load(page) }, [page])

  const change = async (id:number)=>{
    const s = nextStatus[id]
    if(!s) return
    try{setBusyId(id);setError('')
      await updateGrievanceStatus(id, s)
      load(page)
    }catch{ setError('Unable to update grievance status.') }finally{setBusyId(null)}
  }

  return (
    <div>
      <h2>Grievances</h2>
      {error&&<div className="dashboard-state error-state"><p>{error}</p><button onClick={()=>load(page)}>Try again</button></div>}
      {loading?<div className="dashboard-state"><div className="loading-dot"/><p>Loading grievances...</p></div>:!items.length&&!error?<div className="dashboard-state"><p>No grievances found.</p></div>:<ul>
        {items.map(g=> (
          <li key={g.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div><strong>{g.grievance_code}</strong> — {g.client_name}</div>
            <div>{g.description}</div>
            <div>Status: {g.status}</div>
            <div className="button-row"><label>New status<select value={nextStatus[g.id]||''} onChange={e=>setNextStatus(current=>({...current,[g.id]:e.target.value}))}><option value="">Select status</option>{['New','Under Review','Resolved','Closed'].filter(s=>s!==g.status).map(s=><option key={s}>{s}</option>)}</select></label><button disabled={!nextStatus[g.id]||busyId===g.id} onClick={()=>change(g.id)}>{busyId===g.id?'Updating…':'Update status'}</button></div>
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
