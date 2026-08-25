import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import {fetchServiceCatalog,readCachedServices} from '../../services/serviceCatalog'

const POPULAR=['Passport','Income certificate','Scholarship','Government jobs','Aadhaar update']
const categoryName=(service:any)=>typeof service.category==='string'?service.category:service.category?.name||'Other services'
const normalise=(value:string)=>value.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim().replace(/\bgovt\b/g,'government')

export default function SearchPanel(){
  const [q,setQ]=useState('');const [services,setServices]=useState<any[]>(readCachedServices);const [loading,setLoading]=useState(services.length===0);const [error,setError]=useState('');const [category,setCategory]=useState('');const [retry,setRetry]=useState(0)
  const term=q.trim()

  useEffect(()=>{
    let active=true
    setError('')
    if(!services.length)setLoading(true)
    fetchServiceCatalog(retry>0)
      .then(items=>{if(active)setServices(items)})
      .catch((err:any)=>{if(active&&!services.length)setError(err?.code==='ECONNABORTED'?'The service server is waking up slowly. Please try again.':'Services are temporarily unavailable. Please try again.')})
      .finally(()=>{if(active)setLoading(false)})
    return()=>{active=false}
  },[retry])

  const results=useMemo(()=>{if(!term)return[];const tokens=normalise(term).split(' ').filter(Boolean);return services.filter(service=>{const searchable=normalise(`${service.name||''} ${service.description||''} ${service.keywords||''} ${categoryName(service)}`);return tokens.every(token=>searchable.includes(token))})},[services,term])
  const categories=useMemo(()=>Array.from(new Set(results.map(categoryName))).sort(),[results])
  const visible=useMemo(()=>category?results.filter(item=>categoryName(item)===category):results,[results,category])
  const choose=(value:string)=>{setQ(value);setCategory('');document.getElementById('service-search-input')?.focus()}

  return <section className="content-section search-panel-premium" id="service-search" aria-labelledby="service-search-title">
    <div className="section-header inline"><div><span className="eyebrow">Quick search</span><h2 id="service-search-title">What service do you need help with?</h2></div><span className="search-meta" aria-live="polite">{loading?'Loading services':term?`${visible.length} result${visible.length===1?'':'s'}`:'Ready'}</span></div>
    <div className="search-box"><input id="service-search-input" type="search" autoComplete="off" aria-label="Search services" placeholder="Search jobs, scholarships, certificates, schemes..." value={q} onChange={e=>{setQ(e.target.value);setCategory('')}}/>{q&&<button type="button" className="btn-secondary" onClick={()=>setQ('')} aria-label="Clear service search">Clear</button>}</div>
    <div className="popular-searches" aria-label="Popular searches"><strong>Popular Searches</strong><div className="filter-tabs">{POPULAR.map(item=><button type="button" key={item} onClick={()=>choose(item)}>{item}</button>)}</div></div>
    {categories.length>1&&<label className="search-category-filter">Filter results by category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{categories.map(item=><option key={item}>{item}</option>)}</select></label>}
    {loading&&services.length===0&&<div className="empty-state" role="status"><div className="loading-dot"/><p>Loading services… The secure server may take a moment on the first visit.</p></div>}
    {error&&<div className="empty-state error-state" role="alert"><p>{error}</p><button type="button" onClick={()=>setRetry(value=>value+1)}>Try again</button></div>}
    {!loading&&!error&&term&&visible.length===0&&<div className="empty-state"><h3>No services found for “{term}”</h3><p>Try a shorter phrase, another category, or one of the popular searches above.</p><button type="button" className="btn-secondary" onClick={()=>setQ('')}>Browse all categories</button></div>}
    {!loading&&!error&&visible.length>0&&<ul className="service-list" aria-live="polite">{visible.map(service=><li key={service.id} className="service-card"><div className="service-card-top"><span className="service-badge">{categoryName(service)}</span><span className="service-price">Assistance fee from ₹{service.price_inr}</span></div><h3><Link to={`/service/${service.id}`}>{service.name}</Link></h3><p>{service.description}</p><Link className="text-link" to={`/service/${service.id}`}>View details</Link></li>)}</ul>}
  </section>
}
