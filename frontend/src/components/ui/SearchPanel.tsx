import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { apiBase } from '../../services/apiBase'
import { Link } from 'react-router-dom'

const SEARCH_TIMEOUT_MS = 8000

export default function SearchPanel(){
  const [q,setQ] = useState('')
  const [results,setResults] = useState<any[]>([])
  const [loading,setLoading] = useState(false)
  const [error,setError] = useState(false)

  useEffect(()=>{
    const source = axios.CancelToken.source()
    const value = q.trim()
    if(value===''){
      setResults([]); setError(false); setLoading(false); return
    }
    const timer = window.setTimeout(()=>{
      setLoading(true)
      axios.get(`${apiBase}/services/search`,{params:{q:value},cancelToken:source.token,timeout:SEARCH_TIMEOUT_MS}).then(r=>{
        setResults(Array.isArray(r.data) ? r.data : [])
        setError(false)
      }).catch(e=>{ if(!axios.isCancel(e)){ setError(true); setResults([]) } }).finally(()=>setLoading(false))
    },250)
    return ()=>{ window.clearTimeout(timer); source.cancel() }
  },[q])

  return (
    <section className="content-section search-panel-premium" aria-labelledby="service-search-heading">
      <div className="section-header inline"><div><span className="eyebrow">Find a service</span><h2 id="service-search-heading">What do you need help with?</h2><p>Search by service name, exam, card, scholarship, certificate or keyword.</p></div><span className="search-meta">Public access</span></div>
      <div className="search-box"><input aria-label="Search public services" autoComplete="off" placeholder="Try PAN, Aadhaar, voter ID, ePASS, scholarship, POLYCET, EAPCET..." value={q} onChange={e=>setQ(e.target.value)}/></div>
      {loading && <div className="empty-state" role="status">Finding services…</div>}
      {error && <div className="empty-state" role="alert">Search is temporarily unavailable. Please try again.</div>}
      {!loading && !error && q.trim() && results.length===0 && <div className="empty-state"><strong>No matching service found.</strong><p>Try a shorter keyword such as “PAN”, “scholarship”, “exam”, “certificate” or “Aadhaar”.</p></div>}
      {!loading && !error && results.length>0 && <ul className="service-list">{results.map(s=>(<li key={s.id} className="service-card"><div className="service-card-top"><span className="service-badge">{typeof s.category==='string' ? s.category : s.category?.name || 'Public service'}</span><span className="service-price">Assistance ₹{s.price_inr}</span></div><h3><Link to={`/service/${s.id}`}>{s.name}</Link></h3><p>{s.description}</p><Link className="text-link" to={`/service/${s.id}`}>View service &amp; requirements →</Link></li>))}</ul>}
    </section>
  )
}
