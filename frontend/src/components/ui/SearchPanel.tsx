import React,{useEffect,useMemo,useState} from 'react'
import axios from 'axios'
import {apiBase} from '../../services/apiBase'
import {Link} from 'react-router-dom'

const POPULAR=['Passport','Income certificate','Scholarship','Government jobs','Aadhaar update']
const categoryName=(service:any)=>typeof service.category==='string'?service.category:service.category?.name||'Other services'

export default function SearchPanel(){
  const [q,setQ]=useState('');const [results,setResults]=useState<any[]>([]);const [loading,setLoading]=useState(false);const [error,setError]=useState('');const [category,setCategory]=useState('');const [retry,setRetry]=useState(0)
  const term=q.trim()

  useEffect(()=>{
    if(!term){setResults([]);setError('');setLoading(false);setCategory('');return}
    const controller=new AbortController();const timer=window.setTimeout(async()=>{setLoading(true);setError('');try{const response=await axios.get(`${apiBase}/services/search`,{params:{q:term},signal:controller.signal,timeout:15000});setResults(Array.isArray(response.data)?response.data:[])}catch(err:any){if(!axios.isCancel(err)&&err?.code!=='ERR_CANCELED'){setResults([]);setError(err?.code==='ECONNABORTED'?'Search took too long. Please try again.':'Search is temporarily unavailable. Please try again.')}}finally{if(!controller.signal.aborted)setLoading(false)}},250)
    return()=>{window.clearTimeout(timer);controller.abort()}
  },[term,retry])

  const categories=useMemo(()=>Array.from(new Set(results.map(categoryName))).sort(),[results])
  const visible=useMemo(()=>category?results.filter(item=>categoryName(item)===category):results,[results,category])
  const choose=(value:string)=>{setQ(value);setCategory('');document.getElementById('service-search-input')?.focus()}

  return <section className="content-section search-panel-premium" id="service-search" aria-labelledby="service-search-title">
    <div className="section-header inline"><div><span className="eyebrow">Quick search</span><h2 id="service-search-title">What service do you need help with?</h2></div><span className="search-meta" aria-live="polite">{loading?'Searching':term?`${visible.length} result${visible.length===1?'':'s'}`:'Live'}</span></div>
    <div className="search-box"><input id="service-search-input" type="search" autoComplete="off" aria-label="Search services" placeholder="Search jobs, scholarships, certificates, schemes..." value={q} onChange={e=>{setQ(e.target.value);setCategory('')}}/>{q&&<button type="button" className="btn-secondary" onClick={()=>setQ('')} aria-label="Clear service search">Clear</button>}</div>
    <div className="popular-searches" aria-label="Popular searches"><strong>Popular Searches</strong><div className="filter-tabs">{POPULAR.map(item=><button type="button" key={item} onClick={()=>choose(item)}>{item}</button>)}</div></div>
    {categories.length>1&&<label className="search-category-filter">Filter results by category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{categories.map(item=><option key={item}>{item}</option>)}</select></label>}
    {loading&&<div className="empty-state" role="status"><div className="loading-dot"/><p>Searching services…</p></div>}
    {error&&<div className="empty-state error-state" role="alert"><p>{error}</p><button type="button" onClick={()=>setRetry(value=>value+1)}>Try again</button></div>}
    {!loading&&!error&&term&&visible.length===0&&<div className="empty-state"><h3>No services found for “{term}”</h3><p>Try a shorter phrase, another category, or one of the popular searches above.</p><button type="button" className="btn-secondary" onClick={()=>setQ('')}>Browse all categories</button></div>}
    {!loading&&!error&&visible.length>0&&<ul className="service-list" aria-live="polite">{visible.map(service=><li key={service.id} className="service-card"><div className="service-card-top"><span className="service-badge">{categoryName(service)}</span><span className="service-price">₹{service.price_inr}</span></div><h3><Link to={`/service/${service.id}`}>{service.name}</Link></h3><p>{service.description}</p><Link className="text-link" to={`/service/${service.id}`}>View details</Link></li>)}</ul>}
  </section>
}
