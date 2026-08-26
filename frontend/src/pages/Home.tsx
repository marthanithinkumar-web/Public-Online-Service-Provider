import React,{useEffect,useMemo,useState} from 'react'
import { Link } from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import WhyChoose from '../components/ui/WhyChoose'
import HowItWorks from '../components/ui/HowItWorks'
import CategoriesSection from '../components/ui/CategoriesSection'
import {fetchServiceCatalog,readCachedServices} from '../services/serviceCatalog'

export default function Home(){
  const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true))
  useEffect(()=>{let active=true;fetchServiceCatalog(true).then(items=>{if(active)setCatalog(items)}).catch(()=>{});return()=>{active=false}},[])
  const assistanceFeeLabel=useMemo(()=>{
    const fees=Array.from(new Set(catalog.map(service=>Number(service.price_inr)).filter(Number.isFinite))).sort((a,b)=>a-b)
    if(!fees.length)return 'Shown per service'
    return fees.length===1?`₹${fees[0]}`:`From ₹${fees[0]}`
  },[catalog])
  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Trusted public support platform</span>
          <h1>Public Services, Made Easier for You</h1>
          <p>Find trusted assistance for jobs, scholarships, certificates, MeeSeva services, online applications and government schemes—all in one place.</p>
          <SearchPanel variant="hero" />
          <div className="hero-links"><Link className="hero-link-primary" to="/register">Create your account</Link><Link className="hero-link-track" to="/login?returnTo=%2Fmy-orders">Track My Request</Link></div>
        </div>
        <aside className="hero-panel" aria-label="Platform highlights">
          <div className="hero-highlight-grid"><div><strong>90+</strong><span>Service options</span></div><div><strong>10</strong><span>Categories</span></div><div><strong>24/7</strong><span>Online access</span></div><div><strong>Private</strong><span>Citizen-first support</span></div></div>
          <div className="mini-card trust-box"><span className="mini-label">Safe assistance</span><p>We never ask for your OTP, password, PIN or banking-login credentials.</p></div>
        </aside>
      </section>

      <CategoriesSection />
      <ServicesSection />
      <HowItWorks />
      <WhyChoose />

      <section className="content-section privacy-block" id="help">
        <div className="privacy-copy"><span className="eyebrow">Your trust, our priority</span><h2>Clear fees. Safe assistance. No confusion.</h2><p>We are an independent private assistance provider—not a government department or official government portal. We only request information necessary for your selected service.</p><ul className="safety-list"><li>Never share OTPs, passwords, PINs or banking-login details.</li><li>Your assistance fee is separate from government or official charges.</li><li>Every submitted request receives a trackable reference ID.</li></ul></div>
        <div className="home-fee-card"><span>Fee transparency</span><dl><div><dt>Our Assistance Fee</dt><dd>{assistanceFeeLabel}</dd></div><div><dt>Government / Official Fee</dt><dd>As applicable</dd></div></dl><p>Assistance fees are set by the provider. Official charges vary by service and are always shown separately.</p></div>
      </section>
      <section className="home-cta"><div><span className="eyebrow light">Need help now?</span><h2>Find your service and submit a secure request.</h2></div><Link className="btn btn-primary light-btn" to="/#service-search">Search Services</Link></section>
    </div>
  )
}
