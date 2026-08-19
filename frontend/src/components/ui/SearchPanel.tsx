import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { apiBase } from '../../services/apiBase'
import { Link } from 'react-router-dom'

export default function SearchPanel(){
  const [q,setQ] = useState('')
  const [results,setResults] = useState<any[]>([])
  const [loading,setLoading] = useState(false)
  const [error,setError] = useState(false)

  useEffect(()=>{
    const source = axios.CancelToken.source()
    if(q.trim()===''){
      setResults([]); setError(false); setLoading(false); return
    }
    setLoading(true)
    axios.get(`${apiBase}/services/search`,{params:{q},cancelToken:source.token}).then(r=>{
      if(Array.isArray(r.data)) setResults(r.data)
      else setResults([])
      setError(false)
    }).catch(e=>{ if(!axios.isCancel(e)){ setError(true); setResults([]) } }).finally(()=>setLoading(false))
    return ()=>source.cancel()
  },[q])

  return (
    <section className="content-section search-panel-premium">
      <div className="section-header inline"><div><span className="eyebrow">Quick search</span><h2>What service do you need help with?</h2></div><span className="search-meta">Live</span></div>
      <div className="search-box"><input aria-label="Search services" placeholder="Search jobs, scholarships, certificates, schemes..." value={q} onChange={e=>setQ(e.target.value)}/></div>
      {loading && <div className="empty-state">Searching…</div>}
      {error && <div className="empty-state">Search temporarily unavailable.</div>}
      {!loading && !error && results.length>0 && <ul className="service-list">{results.map(s=>(<li key={s.id} className="service-card"><div className="service-card-top"><span className="service-badge">{s.category?.name || 'Service'}</span><span className="service-price">₹{s.price_inr}</span></div><h3><Link to={`/service/${s.id}`}>{s.name}</Link></h3><p>{s.description}</p><Link className="text-link" to={`/service/${s.id}`}>View details</Link></li>))}</ul>}
    </section>
  )
}
