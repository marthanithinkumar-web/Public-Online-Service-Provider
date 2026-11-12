import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import Seo from '../components/ui/Seo'
import {fetchScholarships,Scholarship,scholarshipPath,scholarshipSourceLabel,scholarshipStatusLabel,scholarshipLastVerified} from '../services/scholarships'

type ScholarshipSort='deadline'|'newest'|'title'

export default function Scholarships(){
  const [items,setItems]=useState<Scholarship[]>([]),[q,setQ]=useState(''),[category,setCategory]=useState(''),[education,setEducation]=useState(''),[region,setRegion]=useState(''),[sort,setSort]=useState<ScholarshipSort>('deadline'),[loading,setLoading]=useState(true),[error,setError]=useState('')
  useEffect(()=>{let active=true;fetchScholarships().then(data=>{if(active)setItems(data.items)}).catch(()=>active&&setError('Scholarships are temporarily unavailable.')).finally(()=>active&&setLoading(false));return()=>{active=false}},[])
  const options=useMemo(()=>({categories:Array.from(new Set(items.map(s=>s.category).filter(Boolean))).sort(),education:Array.from(new Set(items.map(s=>s.education_level).filter(Boolean))).sort(),regions:Array.from(new Set(items.map(s=>s.region).filter(Boolean))).sort()}),[items])
  const visible=useMemo(()=>{
    const tokens=q.toLowerCase().split(/\s+/).filter(Boolean)
    const result=items.filter(s=>tokens.every(t=>[s.title,s.provider,s.source_name,s.source_type,s.region,s.education_level,s.category,s.eligibility,s.academic_year].join(' ').toLowerCase().includes(t))).filter(s=>!category||s.category===category).filter(s=>!education||s.education_level===education).filter(s=>!region||s.region===region)
    return result.sort((a,b)=>sort==='title'?a.title.localeCompare(b.title):sort==='newest'?String(b.last_seen_at||b.verified_at||'').localeCompare(String(a.last_seen_at||a.verified_at||'')):String(a.deadline||'9999').localeCompare(String(b.deadline||'9999')))
  },[items,q,category,education,region,sort])
  return <section className="content-section"><Seo title="Scholarships & Application Assistance" description="Search active scholarships, review eligibility and get application assistance." path="/scholarships" index/>
    <div className="section-header"><div><span className="eyebrow">Updated scholarship opportunities</span><h1>Scholarships</h1><p>Search active opportunities and check the eligibility requirements before applying.</p></div></div>
    <div className="scholarship-controls"><label className="search-box"><span className="sr-only">Search scholarships</span><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search scholarship, provider, course, state or category"/></label><label>Category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{options.categories.map(value=><option key={value||'unknown'} value={value||''}>{value}</option>)}</select></label><label>Study level<select value={education} onChange={e=>setEducation(e.target.value)}><option value="">All study levels</option>{options.education.map(value=><option key={value||'unknown'} value={value||''}>{value}</option>)}</select></label><label>Region<select value={region} onChange={e=>setRegion(e.target.value)}><option value="">All regions</option>{options.regions.map(value=><option key={value||'unknown'} value={value||''}>{value}</option>)}</select></label><label>Sort<select value={sort} onChange={e=>setSort(e.target.value as ScholarshipSort)}><option value="deadline">Deadline soonest</option><option value="newest">Newest listings</option><option value="title">Title A–Z</option></select></label></div>
    {!loading&&!error&&<p className="job-results-summary" role="status">{visible.length} active scholarship{visible.length===1?'':'s'}</p>}
    {loading&&<div className="jobs-loading" role="status"><div className="loading-dot"/><p>Loading scholarships…</p></div>}{error&&<p className="info" role="alert">{error}</p>}
    {!loading&&!error&&<div className="service-grid">{visible.map(item=><article className="service-card" key={item.id}><span className="eyebrow">{scholarshipStatusLabel(item)} · {scholarshipSourceLabel(item)}</span><p className="muted">{scholarshipLastVerified(item)}</p><h2>{item.title}</h2><p><strong>{item.provider}</strong></p>{item.education_level&&<p>Study level: {item.education_level}</p>}{item.region&&<p>Region: {item.region}</p>}<p>{item.deadline?`Apply by ${new Date(`${item.deadline}T00:00:00`).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'})}`:'Deadline: see current listing'}</p><Link className="btn btn-primary" to={scholarshipPath(item)}>{item.application_status==='deadline_today'?'Check Official Portal':'View Details & Apply'}</Link></article>)}</div>}
    {!loading&&!error&&visible.length===0&&<div className="empty-dashboard"><h2>No active scholarship matches</h2><p>Try a broader search. Closed applications are removed from the active list.</p></div>}
  </section>
}
