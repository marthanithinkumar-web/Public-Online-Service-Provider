import React,{useEffect,useMemo,useState} from 'react'
import {Link,useLocation} from 'react-router-dom'
import {fetchServiceCatalog,readCachedServices,servicePath} from '../services/serviceCatalog'
import '../styles/home-modern.css'

const CONFIG:Record<string,{title:string;description:string;terms:string[];quick:string[]}>= {
 '/government-services':{title:'Government Services',description:'Browse all available certificate, identity, education, land, welfare, transport, licence and other public-service assistance in one easy place.',terms:[],quick:['Certificates','Identity & ID','Education','Land & Revenue','Transport','Welfare','Business & Licences','Other Services']},
 '/recharge-bills':{title:'Recharge & Bill Payments',description:'Choose the exact recharge or bill type you need, then open it to view details and start your request.',terms:['recharge','bill','electricity','dth','broadband','water','gas','fastag','postpaid','landline'],quick:['Mobile Recharge','Postpaid','DTH','Electricity','Broadband','FASTag','Gas','Other Bills']}
}

function bucketFor(service:any,payment:boolean){
 const text=`${service.name||''} ${service.category||''} ${service.keywords||''}`.toLowerCase()
 if(payment){
  if(text.includes('mobile')&&text.includes('recharge'))return'Mobile Recharge'
  if(text.includes('postpaid'))return'Postpaid'
  if(text.includes('dth'))return'DTH'
  if(text.includes('electric'))return'Electricity'
  if(text.includes('broadband')||text.includes('landline'))return'Broadband'
  if(text.includes('fastag'))return'FASTag'
  if(text.includes('gas'))return'Gas'
  return'Other Bills'
 }
 if(text.includes('certificate')||text.includes('birth')||text.includes('death'))return'Certificates'
 if(text.includes('aadhaar')||text.includes('pan ')||text.includes('voter')||text.includes('passport')||text.includes('identity'))return'Identity & ID'
 if(text.includes('education')||text.includes('school')||text.includes('college')||text.includes('student'))return'Education'
 if(text.includes('land')||text.includes('revenue')||text.includes('property'))return'Land & Revenue'
 if(text.includes('driving')||text.includes('vehicle')||text.includes('transport'))return'Transport'
 if(text.includes('welfare')||text.includes('scheme')||text.includes('ration')||text.includes('pension')||text.includes('health'))return'Welfare'
 if(text.includes('business')||text.includes('licence')||text.includes('license')||text.includes('registration'))return'Business & Licences'
 return'Other Services'
}

export default function ServiceDirectory(){
 const location=useLocation();const config=CONFIG[location.pathname]||CONFIG['/government-services'];const payment=location.pathname==='/recharge-bills'
 const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true));const [loading,setLoading]=useState(catalog.length===0);const [query,setQuery]=useState('');const [active,setActive]=useState('All')
 useEffect(()=>{let mounted=true;fetchServiceCatalog().then(items=>{if(mounted)setCatalog(items)}).catch(()=>{}).finally(()=>{if(mounted)setLoading(false)});return()=>{mounted=false}},[])
 useEffect(()=>{setQuery('');setActive('All')},[location.pathname])
 const scoped=useMemo(()=>catalog.filter(s=>{const hay=`${s.name||''} ${s.category||''} ${s.keywords||''} ${s.description||''}`.toLowerCase();return config.terms.length===0||config.terms.some(term=>hay.includes(term))}),[catalog,config])
 const services=useMemo(()=>{const q=query.trim().toLowerCase();return scoped.filter(s=>{const hay=`${s.name||''} ${s.category||''} ${s.keywords||''} ${s.description||''}`.toLowerCase();return(!q||hay.includes(q))&&(active==='All'||bucketFor(s,payment)===active)})},[scoped,query,active,payment])
 const grouped=useMemo(()=>config.quick.map(name=>({name,items:services.filter(s=>bucketFor(s,payment)===name)})).filter(group=>group.items.length>0),[services,config.quick,payment])
 return <div className="service-directory-page">
  <section className="directory-hero"><div><span className="eyebrow">Easy service access</span><h1>{config.title}</h1><p>{config.description}</p></div><Link className="directory-home-link" to="/">← Back to home</Link></section>
  <section className="directory-toolbar" aria-label={`${config.title} tools`}><label className="directory-search"><span>Search</span><input aria-label={`Search ${config.title}`} placeholder={payment?'Search mobile, DTH, electricity, FASTag…':'Search certificate, Aadhaar, PAN, land, licence…'} value={query} onChange={e=>setQuery(e.target.value)}/></label><div className="directory-count"><strong>{services.length}</strong><span>services found</span></div></section>
  <nav className="directory-chips" aria-label="Service categories"><button type="button" className={active==='All'?'active':''} onClick={()=>setActive('All')}>All</button>{config.quick.map(item=><button type="button" className={active===item?'active':''} key={item} onClick={()=>setActive(item)}>{item}</button>)}</nav>
  {loading?<div className="empty-state" role="status">Loading services…</div>:services.length===0?<div className="empty-state"><h2>No matching services found</h2><p>Try another search or choose a different category.</p><button className="btn btn-primary" type="button" onClick={()=>{setQuery('');setActive('All')}}>Show all services</button></div>:<div className="directory-groups">{grouped.map(group=><section className="directory-group" key={group.name}><header><div><h2>{group.name}</h2><p>{group.items.length} available</p></div></header><div className="directory-card-grid">{group.items.map(s=><article className="directory-card" key={s.id}><div className="directory-card-top"><span>{s.category||group.name}</span><strong>₹{Number(s.price_inr||0)}</strong></div><h3>{s.name}</h3>{s.description&&<p>{s.description}</p>}<Link className="btn btn-primary" to={servicePath(s)}>View details & apply →</Link></article>)}</div></section>)}</div>}
  <section className="directory-help"><div><strong>Not sure which service to choose?</strong><span>Use the search above or contact support and we’ll help you find the right option.</span></div><Link to="/contact">Get help →</Link></section>
 </div>
}
