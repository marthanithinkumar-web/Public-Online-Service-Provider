import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import {fetchServiceCatalog,readCachedServices,servicePath} from '../../services/serviceCatalog'

const preferred=['income certificate','scholarship','government job','aadhaar','birth certificate','ration card']
const categoryName=(service:any)=>typeof service.category==='string'?service.category:service.category?.name||'Public service'

export default function ServicesSection(){
  const [services,setServices]=useState<any[]>(()=>readCachedServices(true))
  const [loading,setLoading]=useState(services.length===0)

  useEffect(()=>{let active=true;fetchServiceCatalog(true).then(items=>{if(active)setServices(items)}).catch(()=>{}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[])

  const popular=useMemo(()=>{
    const available=services.filter(service=>service.is_active!==false)
    const chosen:any[]=[]
    preferred.forEach(term=>{
      const remaining=available.filter(service=>!chosen.includes(service))
      const nameMatch=remaining.find(service=>String(service.name||'').toLowerCase().includes(term))
      const keywordMatch=remaining.find(service=>String(service.keywords||'').toLowerCase().includes(term))
      const match=nameMatch||keywordMatch
      if(match)chosen.push(match)
    })
    available.forEach(service=>{if(chosen.length<6&&!chosen.includes(service))chosen.push(service)})
    return chosen.slice(0,6)
  },[services])

  return <section className="content-section services-section" aria-labelledby="popular-services-title">
    <div className="section-header"><div><span className="eyebrow">Frequently requested</span><h2 id="popular-services-title">Popular Services</h2></div><Link className="text-link" to="/#service-search">View all →</Link></div>
    {loading&&popular.length===0?<div className="empty-state" role="status"><div className="loading-dot"/><p>Loading…</p></div>:<div className="popular-service-grid">{popular.map(service=><article key={service.id} className="popular-service-card"><div className="popular-service-heading"><span className="popular-service-icon" aria-hidden="true">{String(service.name||'S').charAt(0)}</span><div><span className="service-badge">{categoryName(service)}</span><h3>{service.name}</h3></div></div><div className="popular-service-meta"><span><small>Application Assistance Fee</small><strong>{service.price_inr==null?'To be confirmed':`₹${Number(service.price_inr)}`}</strong></span><span><small>Official fee</small><strong>{service.official_fee_status==='known'?`₹${Number(service.official_fee_inr??0)}`:service.official_fee_status==='none'?'₹0':'To be confirmed'}</strong></span></div><Link className="btn btn-secondary small" to={servicePath(service)}>View & apply</Link></article>)}</div>}
  </section>
}
