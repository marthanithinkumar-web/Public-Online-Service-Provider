import React,{useEffect,useMemo,useRef,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {fetchServiceCatalog,readCachedServices,servicePath,serviceSearchTokens} from '../../services/serviceCatalog'

const POPULAR=['Income certificate','Scholarships','Government jobs','Aadhaar update','Birth certificate','Ration card']
const categoryName=(service:any)=>typeof service.category==='string'?service.category:service.category?.name||'Other services'
const normalise=(value:string)=>value.toLowerCase().replace(/[^a-z0-9]+/g,' ').trim().replace(/\bgovt\b/g,'government')

export default function SearchPanel({context='home',variant='section'}:{context?:'home'|'dashboard',variant?:'section'|'hero'}){
  const location=useLocation()
  const inputRef=useRef<HTMLInputElement>(null)
  const [q,setQ]=useState('');const [services,setServices]=useState<any[]>(()=>readCachedServices(true));const [loading,setLoading]=useState(services.length===0);const [error,setError]=useState('');const [category,setCategory]=useState('');const [retry,setRetry]=useState(0)
  const term=q.trim()
  const inputId=context==='dashboard'?'dashboard-service-search-input':'service-search-input'
  const titleId=context==='dashboard'?'dashboard-service-search-title':'service-search-title'

  useEffect(()=>{
    let active=true
    setError('')
    if(!services.length)setLoading(true)
    fetchServiceCatalog(true)
      .then(items=>{if(active)setServices(items)})
      .catch((err:any)=>{if(active&&!services.length)setError(err?.code==='ECONNABORTED'?'The service server is taking too long to respond. Select Try again to reconnect.':'Services are temporarily unavailable. Please try again.')})
      .finally(()=>{if(active)setLoading(false)})
    return()=>{active=false}
  },[retry])

  useEffect(()=>{
    if(context!=='home')return
    const requested=new URLSearchParams(location.search).get('search')
    if(requested){setQ(requested);setCategory('')}
    if(location.hash==='#service-search')requestAnimationFrame(()=>{document.getElementById('service-search')?.scrollIntoView({behavior:'smooth',block:'center'});inputRef.current?.focus()})
  },[context,location.hash,location.search])

  const results=useMemo(()=>{if(!term)return[];const tokens=serviceSearchTokens(term);if(!tokens.length)return services;return services.filter(service=>{const searchable=normalise(`${service.name||''} ${service.catalog_name||''} ${service.description||''} ${service.keywords||''} ${categoryName(service)}`);return tokens.every(token=>searchable.includes(token))})},[services,term])
  const categories=useMemo(()=>Array.from(new Set(results.map(categoryName))).sort(),[results])
  const visible=useMemo(()=>category?results.filter(item=>categoryName(item)===category):results,[results,category])
  const choose=(value:string)=>{setQ(value);setCategory('');inputRef.current?.focus()}

  return <section className={variant==='hero'?'hero-search-panel':'content-section search-panel-premium'} id="service-search" aria-labelledby={titleId}>
    {variant==='section'?<div className="section-header inline"><div><span className="eyebrow">{context==='dashboard'?'Explore services':'Quick search'}</span><h2 id={titleId}>What service do you need help with?</h2></div><span className="search-meta" aria-live="polite">{loading?'Loading services':term?`${visible.length} result${visible.length===1?'':'s'}`:'Ready'}</span></div>:<h2 className="visually-hidden" id={titleId}>Search public services</h2>}
    <div className="search-box homepage-search-box"><span className="search-input-icon" aria-hidden="true">⌕</span><input ref={inputRef} id={inputId} type="search" autoComplete="off" aria-label="Search services" placeholder="Search for a service, certificate, job or scholarship" value={q} onChange={e=>{setQ(e.target.value);setCategory('')}}/>{q?<button type="button" className="btn-secondary search-submit" onClick={()=>{setQ('');setCategory('');inputRef.current?.focus()}} aria-label="Clear service search">Clear</button>:<button type="button" className="search-submit" onClick={()=>inputRef.current?.focus()}>Search</button>}</div>
    <div className="popular-searches" aria-label="Popular searches"><strong>Popular Searches</strong><div className="filter-tabs">{POPULAR.map(item=><button type="button" key={item} onClick={()=>choose(item)}>{item}</button>)}</div></div>
    {term&&<Link className="job-search-forward" to={`/jobs?q=${encodeURIComponent(term)}`}>Search current official job notices for “{term}” →</Link>}
    {categories.length>1&&<label className="search-category-filter">Filter results by category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="">All categories</option>{categories.map(item=><option key={item}>{item}</option>)}</select></label>}
    {loading&&services.length===0&&<div className="empty-state" role="status"><div className="loading-dot"/><p>Loading services… The secure server may take a moment on the first visit.</p></div>}
    {error&&<div className="empty-state error-state" role="alert"><p>{error}</p><button type="button" onClick={()=>setRetry(value=>value+1)}>Try again</button></div>}
    {!loading&&!error&&term&&visible.length===0&&<div className="empty-state"><h3>No services found for “{term}”</h3><p>Try a shorter phrase, another category, or one of the popular searches above.</p><button type="button" className="btn-secondary" onClick={()=>setQ('')}>Browse all categories</button></div>}
    {!loading&&!error&&visible.length>0&&<ul className="service-list" aria-live="polite">{visible.map(service=><li key={service.id} className="service-card"><div className="service-card-top"><span className="service-badge">{categoryName(service)}</span><span className="service-price">Applicable Assistance Fee ₹{service.price_inr}</span></div><h3><Link to={servicePath(service)}>{service.name}</Link></h3><Link className="text-link" to={servicePath(service)}>View & apply</Link></li>)}</ul>}
  </section>
}
