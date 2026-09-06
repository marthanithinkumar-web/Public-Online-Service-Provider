import React,{useEffect,useMemo,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {PROVIDER} from '../services/config'
import {fetchServiceCatalog,readCachedServices,servicePath} from '../services/serviceCatalog'

const CATEGORY_ROUTES:Record<string,{title:string;query:string}>={
 jobs:{title:'Government Jobs',query:'jobs'},
 scholarships:{title:'Scholarships',query:'scholarship'},
 meeseva:{title:'MeeSeva / Public Services',query:'meeseva'},
 certificates:{title:'MeeSeva Certificates',query:'certificate'},
 schemes:{title:'Government Schemes',query:'scheme'},
}
function matches(service:any,query:string){
 const hay=[service?.name,service?.catalog_name,service?.category,service?.keywords,service?.description].filter(Boolean).join(' ').toLowerCase()
 if(query==='certificate')return /certificate|birth|death|caste|community|income|residence|domicile|nativity/.test(hay)
 return hay.includes(query.toLowerCase())
}

export default function Category(){
 const location=useLocation();const slug=location.pathname.replace(/^\/+|\/+$/g,'').toLowerCase();const category=CATEGORY_ROUTES[slug]||{title:'Public Services',query:slug};const cached=useMemo(()=>readCachedServices(true).filter(item=>matches(item,category.query)),[category.query]);const [services,setServices]=useState<any[]>(cached);const [loading,setLoading]=useState(cached.length===0);const [error,setError]=useState('');const [retry,setRetry]=useState(0)
 useEffect(()=>{let active=true;if(!services.length)setLoading(true);setError('');fetchServiceCatalog(retry>0).then(items=>{if(active)setServices(items.filter(item=>matches(item,category.query)))}).catch(()=>{if(active&&!services.length)setError('Unable to refresh services right now. Please try again.')} ).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[category.query,retry])
 return <div className="category-page"><div className="form-hero"><span className="eyebrow">Services</span><h1>{category.title}</h1></div><div className="section-header inline"><div><h2>Available services</h2></div><span className="search-meta">{services.length}</span></div>{loading&&services.length===0?<div className="empty-state" role="status">Loading…</div>:error&&services.length===0?<div className="empty-state"><p className="info" role="alert">{error}</p><button className="btn btn-primary" type="button" onClick={()=>setRetry(value=>value+1)}>Try again</button></div>:services.length===0?<div className="empty-state"><h2>No services found</h2><Link className="btn btn-primary" to="/government-services">Browse services</Link></div>:<ul className="service-list">{services.map(s=><li key={s.id} className="service-card"><div className="service-card-top"><span className="service-badge">{s.category||category.title}</span><span className="service-price">Applicable Assistance Fee ₹{s.price_inr}</span></div><h3><Link to={servicePath(s)}>{s.name}</Link></h3><Link className="text-link" to={servicePath(s)}>View & apply</Link></li>)}</ul>}<p className="provider-note">Need help? <a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a></p></div>
}
