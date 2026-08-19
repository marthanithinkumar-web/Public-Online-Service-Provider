import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {Link,useParams} from 'react-router-dom'
import {apiBase} from '../services/apiBase'
import {PROVIDER} from '../services/config'

export default function Category(){
 const {name}=useParams();const [services,setServices]=useState<any[]>([]);const [loading,setLoading]=useState(true);const [error,setError]=useState('');const title=(name||'Services').replace(/-/g,' ')
 useEffect(()=>{if(!name)return;let active=true;setLoading(true);axios.get(`${apiBase}/services/search`,{params:{q:name}}).then(r=>{if(active)setServices(Array.isArray(r.data)?r.data:[])}).catch(()=>{if(active)setError('Unable to load services right now. Please try again.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[name])
 return <div className="category-page"><div className="form-hero"><span className="eyebrow">Explore services</span><h1 style={{textTransform:'capitalize'}}>{title}</h1><p>Find application and document assistance for {title}. We provide independent support and clear guidance.</p></div><div className="section-header inline"><div><span className="eyebrow">Available now</span><h2>Services in this category</h2></div><span className="search-meta">{services.length} available</span></div>{loading?<div className="empty-state">Loading services…</div>:error?<p className="info" role="alert">{error}</p>:services.length===0?<div className="empty-state"><h2>No services found</h2><p>Try another category or search from the homepage.</p><Link className="btn btn-primary" to="/">Search services</Link></div>:<ul className="service-list">{services.map(s=><li key={s.id} className="service-card"><div className="service-card-top"><span className="service-badge">{title}</span><span className="service-price">₹{s.price_inr}</span></div><h3><Link to={`/service/${s.id}`}>{s.name}</Link></h3><p>{s.description}</p><Link className="text-link" to={`/service/${s.id}`}>View service details →</Link></li>)}</ul>}<p className="provider-note">Need help choosing? Contact {PROVIDER.name} at <a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a>.</p></div>
}
