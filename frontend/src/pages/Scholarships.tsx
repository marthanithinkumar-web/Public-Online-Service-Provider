import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import Seo from '../components/ui/Seo'
import {fetchScholarships,Scholarship,scholarshipPath} from '../services/scholarships'

export default function Scholarships(){
  const [items,setItems]=useState<Scholarship[]>([]),[q,setQ]=useState(''),[loading,setLoading]=useState(true),[error,setError]=useState('')
  useEffect(()=>{let active=true;fetchScholarships().then(data=>{if(active)setItems(data.items)}).catch(()=>active&&setError('Scholarships are temporarily unavailable.')).finally(()=>active&&setLoading(false));return()=>{active=false}},[])
  const visible=useMemo(()=>{const tokens=q.toLowerCase().split(/\s+/).filter(Boolean);return items.filter(s=>tokens.every(t=>[s.title,s.provider,s.region,s.education_level,s.category,s.eligibility].join(' ').toLowerCase().includes(t)))},[items,q])
  return <section className="content-section"><Seo title="Scholarships & Application Assistance" description="Search active scholarships, review eligibility and get application assistance." path="/scholarships" index/>
    <div className="section-header"><div><span className="eyebrow">Updated scholarship opportunities</span><h1>Scholarships</h1><p>Search active opportunities and check the eligibility requirements before applying.</p></div></div>
    <label className="search-box"><span className="sr-only">Search scholarships</span><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search scholarship, provider, course, state or category"/></label>
    {loading&&<div className="jobs-loading" role="status"><div className="loading-dot"/><p>Loading scholarships…</p></div>}{error&&<p className="info" role="alert">{error}</p>}
    {!loading&&!error&&<div className="service-grid">{visible.map(item=><article className="service-card" key={item.id}><span className="eyebrow">{item.source_name}</span><h2>{item.title}</h2><p><strong>{item.provider}</strong></p>{item.education_level&&<p>Study level: {item.education_level}</p>}{item.region&&<p>Region: {item.region}</p>}<p>{item.deadline?`Apply by ${new Date(`${item.deadline}T00:00:00`).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}`:'Deadline: see current listing'}</p><Link className="btn btn-primary" to={scholarshipPath(item)}>View Details & Apply</Link></article>)}</div>}
    {!loading&&!error&&visible.length===0&&<div className="empty-dashboard"><h2>No active scholarship matches</h2><p>Try a broader search. Closed applications are removed from the active list.</p></div>}
  </section>
}
