import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'
import { apiBase } from '../services/apiBase'

const categories = [
  { name: 'Jobs', description: 'Public and private job application support', icon: '💼' },
  { name: 'Scholarships', description: 'Find financial aid and education support', icon: '🎓' },
  { name: 'MeeSeva', description: 'Certificates and local government services', icon: '🏛️' },
  { name: 'Certificates', description: 'Birth, domicile, income and identity support', icon: '📄' },
  { name: 'Government Schemes', description: 'Eligibility guidance and application help', icon: '🏛️' },
]

const steps = [
  { title: 'Tell us what you need', text: 'Search for the service or category you need help with.' },
  { title: 'Share your details', text: 'Submit your requirement and upload documents securely.' },
  { title: 'We handle the process', text: 'Our team reviews your request and helps you move forward with confidence.' },
]

export default function Home(){
  const [q, setQ] = useState('')
  const [results, setResults] = useState<any[]>([])
  const [searchError, setSearchError] = useState(false)

  useEffect(()=>{
    const source = axios.CancelToken.source()
    const doSearch = async ()=>{
      try{
        const res = await axios.get(`${apiBase}/services/search`, { params: { q }, cancelToken: source.token })
        if (Array.isArray(res.data)) {
          setResults(res.data)
          setSearchError(false)
        } else {
          setResults([])
          setSearchError(true)
        }
      }catch(err){
        if(!axios.isCancel(err)) {
          setResults([])
          setSearchError(true)
          console.error(err)
        }
      }
    }
    const t = setTimeout(()=>{ doSearch() }, 200)
    return ()=>{ clearTimeout(t); source.cancel() }
  }, [q])

  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Trusted public support platform</span>
          <h1>Public Services, Made Simple.</h1>
          <p>Get reliable assistance with government jobs, scholarships, certificates, public services and government schemes — all in one place.</p>
          <div className="cta-row"><Link className="btn btn-primary" to="/jobs">Explore Services</Link><Link className="btn btn-secondary" to="/register">Get Started</Link></div>
          <div className="hero-stats"><div><strong>20+</strong><span>Services</span></div><div><strong>6</strong><span>Categories</span></div><div><strong>24/7</strong><span>Online Access</span></div><div><strong>Citizen First</strong><span>Approach</span></div></div>
        </div>
        <div className="hero-panel"><div className="mini-card"><span className="mini-label">Popular searches</span><ul><li>Income certificate</li><li>Job application help</li><li>Scholarship guidance</li><li>Government scheme support</li></ul></div><div className="mini-card trust-box"><span className="mini-label">Privacy first</span><p>Your documents and details are handled with care and only used for your requested service.</p></div></div>
      </section>
      <section className="content-section"><div className="section-header"><div><span className="eyebrow">Browse categories</span><h2>Find the service you need</h2></div></div><div className="category-grid">{categories.map((category)=><Link key={category.name} className="category-card" to={category.name==='Jobs'?'/jobs':category.name==='Scholarships'?'/scholarships':category.name==='MeeSeva'?'/meeseva':category.name==='Certificates'?'/certificates':'/schemes'}><span className="category-icon">{category.icon}</span><h3>{category.name}</h3><p>{category.description}</p></Link>)}</div></section>
      <section className="search-panel content-section"><div className="section-header inline"><div><span className="eyebrow">Quick search</span><h2>Search services and applications</h2></div><span className="search-meta">Live results</span></div><div className="search-box"><input aria-label="Search services" placeholder="Search services (e.g. residence, job, certificate, scholarship)" value={q} onChange={e=>setQ(e.target.value)}/></div>{searchError?<div className="empty-state" role="status">Service search is temporarily unavailable. Please try again in a moment.</div>:results.length===0&&q.trim()===''?<div className="empty-state">Start typing to find the right public service.</div>:results.length===0?<div className="empty-state">No matching services found. Try a broader keyword.</div>:null}<ul className="service-list">{results.map(service=><li key={service.id} className="service-card"><div className="service-card-top"><span className="service-badge">Service</span><span className="service-price">₹{service.price_inr}</span></div><h3><Link to={`/service/${service.id}`}>{service.name}</Link></h3><p>{service.description}</p><Link className="text-link" to={`/service/${service.id}`}>View details</Link></li>)}</ul></section>
      <section className="content-section"><div className="section-header"><div><span className="eyebrow">How it works</span><h2>Simple support in three steps</h2></div></div><div className="steps-grid">{steps.map((step,index)=><div className="step-card" key={step.title}><span className="step-number">0{index+1}</span><h3>{step.title}</h3><p>{step.text}</p></div>)}</div></section>
      <section className="content-section privacy-block"><div className="privacy-copy"><span className="eyebrow">Safety & privacy</span><h2>Your information stays protected.</h2><p>We only request the information needed for your service requirement, keep your data private, and guide you securely through the process. We do not represent a government department and we are committed to privacy-first assistance.</p></div><div className="trust-points"><div>Private document handling</div><div>Secure service request flow</div><div>Clear communication</div></div></section>
      <section className="home-cta"><div><span className="eyebrow light">Need help now?</span><h2>Request assistance and let us guide your application.</h2></div><Link className="btn btn-primary light-btn" to="/register">Request Assistance</Link></section>
    </div>
  )
}
