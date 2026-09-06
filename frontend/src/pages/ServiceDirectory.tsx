import React,{useEffect,useMemo,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {fetchServiceCatalog,readCachedServices,servicePath} from '../services/serviceCatalog'

const CONFIG:Record<string,{title:string;description:string;terms:string[]}>= {
 '/government-services':{title:'Government Services',description:'Browse all available certificate, identity, education, land, welfare, transport, licence and other public-service assistance in one place.',terms:[]},
 '/recharge-bills':{title:'Recharge & Bill Payments',description:'Choose from available mobile recharge, DTH, broadband, FASTag, gas and supported bill-payment assistance.',terms:['recharge','bill','electricity','dth','broadband','water','gas','fastag','postpaid','landline']}
}

export default function ServiceDirectory(){
 const location=useLocation();const config=CONFIG[location.pathname]||CONFIG['/government-services']
 const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true));const [loading,setLoading]=useState(catalog.length===0);const [query,setQuery]=useState('')
 useEffect(()=>{let active=true;fetchServiceCatalog().then(items=>{if(active)setCatalog(items)}).catch(()=>{}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[])
 const services=useMemo(()=>{const q=query.trim().toLowerCase();return catalog.filter(s=>{const hay=`${s.name||''} ${s.category||''} ${s.keywords||''} ${s.description||''}`.toLowerCase();const inScope=config.terms.length===0||config.terms.some(term=>hay.includes(term));return inScope&&(!q||hay.includes(q))})},[catalog,config,query])
 return <div className="category-page service-directory-page"><div className="form-hero"><span className="eyebrow">Easy service access</span><h1>{config.title}</h1><p>{config.description}</p></div><div className="search-bar"><input aria-label={`Search ${config.title}`} placeholder={`Search ${config.title.toLowerCase()}…`} value={query} onChange={e=>setQuery(e.target.value)}/></div><div className="section-header inline"><div><h2>Available services</h2><p>Select a service to view details and start your request.</p></div><span className="search-meta">{services.length}</span></div>{loading?<div className="empty-state" role="status">Loading services…</div>:services.length===0?<div className="empty-state"><h2>No matching services found</h2><p>Try a different search.</p></div>:<ul className="service-list">{services.map(s=><li key={s.id} className="service-card"><div className="service-card-top"><span className="service-badge">{s.category||config.title}</span><span className="service-price">Applicable Assistance Fee ₹{Number(s.price_inr||0)}</span></div><h3><Link to={servicePath(s)}>{s.name}</Link></h3>{s.description&&<p>{s.description}</p>}<Link className="btn btn-primary" to={servicePath(s)}>View & apply</Link></li>)}</ul>}</div>
}
