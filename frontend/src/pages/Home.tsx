import React,{useEffect,useMemo,useState} from 'react'
import { Link } from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import WhyChoose from '../components/ui/WhyChoose'
import HowItWorks from '../components/ui/HowItWorks'
import CategoriesSection from '../components/ui/CategoriesSection'
import {fetchServiceCatalog,readCachedServices} from '../services/serviceCatalog'
import axios from 'axios'
import {apiBase} from '../services/apiBase'

export default function Home(){
  const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true))
  const [reviews,setReviews]=useState<any[]>([])
  useEffect(()=>{let active=true;fetchServiceCatalog(true).then(items=>{if(active)setCatalog(items)}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/reviews/public`,{timeout:12000}).then(response=>{if(active)setReviews((response.data||[]).slice(0,6))}).catch(()=>{});return()=>{active=false}},[])
  const assistanceFeeLabel=useMemo(()=>{
    const fees=Array.from(new Set(catalog.map(service=>Number(service.price_inr)).filter(Number.isFinite))).sort((a,b)=>a-b)
    if(!fees.length)return 'Shown per service'
    return fees.length===1?`₹${fees[0]}`:`From ₹${fees[0]}`
  },[catalog])
  const categoryCount=useMemo(()=>new Set(catalog.map(service=>service.category).filter(Boolean)).size,[catalog])
  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Trusted public support platform</span>
          <h1>Public Online Service Provider</h1>
          <p><strong>Public services, made easier for you.</strong> Find independent assistance for PAN cards, government jobs, scholarships, certificates, MeeSeva services, online applications and government schemes—all in one place.</p>
          <SearchPanel variant="hero" />
          <div className="hero-links"><Link className="hero-link-primary" to="/register">Create your account</Link><Link className="hero-link-track" to="/login?returnTo=%2Fmy-orders">Track My Request</Link></div>
        </div>
        <aside className="hero-panel" aria-label="Platform highlights">
          <div className="hero-highlight-grid"><div><strong>{catalog.length||'100+'}</strong><span>Service options</span></div><div><strong>{categoryCount||'10+'}</strong><span>Categories</span></div><div><strong>24/7</strong><span>Online access</span></div><div><strong>Private</strong><span>Citizen-first support</span></div></div>
          <div className="mini-card trust-box"><span className="mini-label">Safe assistance</span><p>We never ask for your OTP, password, PIN or banking-login credentials.</p></div>
        </aside>
      </section>

      <CategoriesSection />
      <ServicesSection />
      <HowItWorks />
      <WhyChoose />

      {reviews.length>0&&<section className="content-section" aria-labelledby="client-reviews-title"><div className="section-header"><div><span className="eyebrow">Verified feedback</span><h2 id="client-reviews-title">What clients say</h2><p className="section-intro">Only moderated reviews from completed service requests are displayed. Client identities remain private.</p></div></div><div className="review-grid">{reviews.map(review=><article className="review-card" key={review.id}><div className="review-stars" aria-label={`${review.rating} out of 5 stars`}>{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</div><p>{review.comment||'Service completed successfully.'}</p><footer><strong>{review.reviewer}</strong>{review.service&&<span>{review.service}</span>}</footer></article>)}</div></section>}

      <section className="content-section privacy-block" id="help">
        <div className="privacy-copy"><span className="eyebrow">Your trust, our priority</span><h2>Clear fees. Safe assistance. No confusion.</h2><p>We are an independent private assistance provider—not a government department or official government portal. We only request information necessary for your selected service.</p><ul className="safety-list"><li>Never share OTPs, passwords, PINs or banking-login details.</li><li>Your assistance fee is separate from government or official charges.</li><li>Every submitted request receives a trackable reference ID.</li></ul></div>
        <div className="home-fee-card"><span>Fee transparency</span><dl><div><dt>Our Assistance Fee</dt><dd>{assistanceFeeLabel}</dd></div><div><dt>Government / Official Fee</dt><dd>As applicable</dd></div></dl><p>Assistance fees are set by the provider. Official charges vary by service and are always shown separately.</p></div>
      </section>
      <section className="home-cta"><div><span className="eyebrow light">Need help now?</span><h2>Find your service and submit a secure request.</h2></div><Link className="btn btn-primary light-btn" to="/#service-search">Search Services</Link></section>
    </div>
  )
}
