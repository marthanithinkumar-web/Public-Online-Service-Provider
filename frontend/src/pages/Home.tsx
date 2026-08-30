import React,{useEffect,useMemo,useState} from 'react'
import { Link } from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import CategoriesSection from '../components/ui/CategoriesSection'
import {fetchServiceCatalog,readCachedServices} from '../services/serviceCatalog'
import axios from 'axios'
import {apiBase} from '../services/apiBase'

export default function Home(){
  const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true))
  const [reviews,setReviews]=useState<any[]>([])
  const [homepageFee,setHomepageFee]=useState<number>(30)
  useEffect(()=>{let active=true;fetchServiceCatalog(true).then(items=>{if(active)setCatalog(items)}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/reviews/public`,{timeout:12000}).then(response=>{if(active)setReviews((response.data||[]).slice(0,6))}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/services/homepage-assistance-fee`,{timeout:12000}).then(response=>{const value=Number(response.data?.price_inr);if(active&&Number.isFinite(value)&&value>=0)setHomepageFee(value)}).catch(()=>{});return()=>{active=false}},[])
  const categoryCount=useMemo(()=>new Set(catalog.map(service=>service.category).filter(Boolean)).size,[catalog])
  return (
    <div className="home-page">
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow">Trusted public support platform</span>
          <h1>Public Online Service Provider</h1>
          <p>Find a service, submit your request and track it online.</p>
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

      {reviews.length>0&&<section className="content-section" aria-labelledby="client-reviews-title"><div className="section-header"><div><span className="eyebrow">Client feedback</span><h2 id="client-reviews-title">Ratings & suggestions</h2></div></div><div className="review-grid">{reviews.map(review=><article className="review-card" key={review.id}><div className="review-stars" aria-label={`${review.rating} out of 5 stars`}>{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</div><p>{review.comment||'Thank you.'}</p><footer><strong>{review.reviewer}</strong>{review.service&&<span>{review.service}</span>}</footer></article>)}</div></section>}

      <section className="content-section privacy-block simplified-home-fee" id="help">
        <div className="privacy-copy"><span className="eyebrow">Fees</span><h2>Application Assistance Fee</h2><p>Shown before you submit. Government or official fees are separate.</p></div>
        <div className="home-fee-card"><span>Application Assistance Fee</span><dl><div><dt>Standard fee</dt><dd>₹{homepageFee}</dd></div><div><dt>Government / Official Fee</dt><dd>As applicable</dd></div></dl></div>
      </section>
      <section className="home-cta"><div><h2>Ready to apply?</h2></div><Link className="btn btn-primary light-btn" to="/#service-search">Find service</Link></section>
    </div>
  )
}
