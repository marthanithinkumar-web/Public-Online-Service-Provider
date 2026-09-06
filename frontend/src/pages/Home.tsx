import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import CategoriesSection from '../components/ui/CategoriesSection'
import LatestJobs from '../components/jobs/LatestJobs'
import {fetchServiceCatalog,isHomepageHighlightEligible,readCachedServices,servicePath} from '../services/serviceCatalog'
import {fetchScholarships,Scholarship,scholarshipPath} from '../services/scholarships'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import '../styles/home-modern.css'

const crucialTerms=['pan','income certificate','caste certificate']
const paymentTerms=['recharge','bill payment','electricity','dth','broadband','water bill','gas bill']

export default function Home(){
  const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true))
  const [scholarships,setScholarships]=useState<Scholarship[]>([])
  const [reviews,setReviews]=useState<any[]>([])
  const [homepageFee,setHomepageFee]=useState<number>(30)

  useEffect(()=>{let active=true;fetchServiceCatalog().then(items=>{if(active)setCatalog(items)}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;fetchScholarships().then(data=>{if(active)setScholarships((data.items||[]).slice(0,4))}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/services/homepage-assistance-fee`,{timeout:6000}).then(response=>{const value=Number(response.data?.price_inr);if(active&&Number.isFinite(value)&&value>=0)setHomepageFee(value)}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{
    let active=true
    const preload=()=>{
      import('./ServiceDetail');import('./Login');import('./Jobs');import('./Scholarships')
      axios.get(`${apiBase}/reviews/public`,{timeout:6000}).then(response=>{if(active)setReviews((response.data||[]).slice(0,3))}).catch(()=>{})
    }
    const idle=(window as any).requestIdleCallback
    const handle=idle?idle(preload,{timeout:2500}):window.setTimeout(preload,1200)
    return()=>{active=false;if(idle)(window as any).cancelIdleCallback?.(handle);else window.clearTimeout(handle)}
  },[])

  const crucial=useMemo(()=>{const eligible=catalog.filter(isHomepageHighlightEligible);const selected:any[]=[];crucialTerms.forEach(term=>{const match=eligible.find(service=>!selected.includes(service)&&`${service.name} ${service.keywords||''}`.toLowerCase().includes(term));if(match)selected.push(match)});eligible.forEach(service=>{if(selected.length<3&&!selected.includes(service))selected.push(service)});return selected.slice(0,3)},[catalog])
  const paymentServices=useMemo(()=>catalog.filter(service=>paymentTerms.some(term=>`${service.name} ${service.category||''} ${service.keywords||''}`.toLowerCase().includes(term))).slice(0,6),[catalog])
  const mobileRecharge=paymentServices.find(service=>`${service.name} ${service.keywords||''}`.toLowerCase().includes('recharge'))
  const billPayment=paymentServices.find(service=>`${service.name} ${service.category||''} ${service.keywords||''}`.toLowerCase().includes('bill'))

  return <div className="home-page redesigned-home modern-access-home">
    <section className="hero concept-hero modern-home-hero">
      <div className="hero-copy"><span className="eyebrow light">Jobs • Scholarships • Services</span><h1>Find opportunities and essential services without confusion</h1><p>Search current jobs and scholarships first, then access public-service, recharge and bill-payment assistance from one clear place.</p><SearchPanel variant="hero"/><div className="hero-links"><Link className="hero-link-primary" to="/jobs">Browse latest jobs</Link><Link className="hero-link-track" to="/scholarships">Find scholarships</Link></div></div>
      <aside className="hero-panel" aria-label="Quick access"><div className="hero-safety-card"><span className="safety-shield">✓</span><div><strong>Simple and secure</strong><p>Clear steps, transparent fees and no requests for OTPs, PINs, CVVs or passwords.</p></div></div><div className="hero-highlight-grid"><div><strong>Daily</strong><span>Job checks</span></div><div><strong>Current</strong><span>Scholarships</span></div><div><strong>{catalog.length||'100+'}</strong><span>Services</span></div><div><strong>Mobile</strong><span>Friendly access</span></div></div></aside>
    </section>

    <section className="home-priority-grid" aria-label="Primary homepage options">
      <Link className="home-priority-card jobs" to="/jobs"><span className="priority-icon">▣</span><div><span className="eyebrow">Updated opportunities</span><h2>Latest Job Updates</h2><p>Government and private opportunities with clear deadlines and source details.</p><strong>View jobs →</strong></div></Link>
      <Link className="home-priority-card scholarships" to="/scholarships"><span className="priority-icon">◆</span><div><span className="eyebrow">Education opportunities</span><h2>Scholarships</h2><p>Explore active central, state and other scholarship opportunities in one place.</p><strong>View scholarships →</strong></div></Link>
    </section>

    <LatestJobs/>

    <section className="content-section home-scholarships" aria-labelledby="home-scholarships-title">
      <div className="section-header"><div><span className="eyebrow">For students</span><h2 id="home-scholarships-title">Latest Scholarships</h2><p>Open an opportunity directly or browse the complete scholarship list.</p></div><Link className="text-link" to="/scholarships">View all scholarships →</Link></div>
      {scholarships.length>0?<div className="home-scholarship-grid">{scholarships.map(item=><Link className="home-scholarship-card" key={item.id} to={scholarshipPath(item)}><span className="scholarship-badge">Scholarship</span><h3>{item.title}</h3><p>{item.provider}</p><small>{item.deadline?`Last date: ${item.deadline}`:'Check details for deadline'}</small><strong>View details →</strong></Link>)}</div>:<div className="home-inline-loading">Scholarships are loading. You can open the full scholarship page anytime.</div>}
    </section>

    <section className="content-section home-quick-actions" aria-labelledby="quick-actions-title"><div className="section-header"><div><span className="eyebrow">Quick access</span><h2 id="quick-actions-title">What do you want to do?</h2></div></div><div className="quick-action-grid"><Link to="/#service-search"><strong>Find a service</strong><span>Search certificates, IDs, schemes and more →</span></Link><Link to="/my-orders"><strong>Track a request</strong><span>See status, messages and payments →</span></Link><Link to={mobileRecharge?servicePath(mobileRecharge):'/#service-search'}><strong>Mobile recharge</strong><span>Start recharge assistance →</span></Link><Link to={billPayment?servicePath(billPayment):'/#service-search'}><strong>Pay a bill</strong><span>Find supported bill-payment assistance →</span></Link></div></section>

    <section className="content-section crucial-services home-lower-section" aria-labelledby="crucial-services-title"><div className="section-header"><div><span className="eyebrow">Frequently needed</span><h2 id="crucial-services-title">Popular Services</h2></div><Link className="text-link" to="/#service-search">View all services →</Link></div><div className="crucial-service-grid">{crucial.map((service,index)=><Link className="crucial-service-card" to={servicePath(service)} key={service.id}><span className={`crucial-icon tone-${index+1}`} aria-hidden="true">{index===0?'▤':index===1?'▧':'◆'}</span><div><h3>{service.name}</h3><p>{service.description}</p><small>Applicable Assistance Fee ₹{Number(service.price_inr||0)}</small></div><span className="crucial-arrow" aria-hidden="true">›</span></Link>)}</div></section>

    <section className="content-section crucial-services home-lower-section" aria-labelledby="recharge-bills-title"><div className="section-header"><div><span className="eyebrow">Recharge & bills</span><h2 id="recharge-bills-title">Recharge & Bill Payments</h2></div><Link className="text-link" to="/#service-search">View all services →</Link></div><div className="crucial-service-grid"><Link className="crucial-service-card" to={mobileRecharge?servicePath(mobileRecharge):'/#service-search'}><span className="crucial-icon tone-1" aria-hidden="true">▣</span><div><h3>Mobile Recharge</h3><p>{mobileRecharge?.description||'Recharge supported mobile connections through the available assistance service.'}</p><small>Assistance Fee ₹{Number(mobileRecharge?.price_inr??10)}</small></div><span className="crucial-arrow" aria-hidden="true">›</span></Link><Link className="crucial-service-card" to={billPayment?servicePath(billPayment):'/#service-search'}><span className="crucial-icon tone-2" aria-hidden="true">▤</span><div><h3>Bill Payments</h3><p>{billPayment?.description||'Find available electricity, DTH, broadband, water, gas and other bill-payment assistance.'}</p><small>Assistance Fee ₹{Number(billPayment?.price_inr??10)}</small></div><span className="crucial-arrow" aria-hidden="true">›</span></Link></div></section>

    <div className="home-lower-section"><CategoriesSection/><ServicesSection/></div>

    {reviews.length>0&&<section className="content-section home-lower-section" aria-labelledby="client-reviews-title"><div className="section-header"><div><span className="eyebrow">Client feedback</span><h2 id="client-reviews-title">Ratings & suggestions</h2></div></div><div className="review-grid">{reviews.map(review=><article className="review-card" key={review.id}><div className="review-stars" aria-label={`${review.rating} out of 5 stars`}>{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</div><p>{review.comment||'Thank you.'}</p><footer><strong>{review.reviewer}</strong>{review.service&&<span>{review.service}</span>}</footer></article>)}</div></section>}

    <section className="content-section privacy-block simplified-home-fee home-lower-section" id="help"><div className="privacy-copy"><span className="eyebrow">Transparent fees</span><h2>Know the charges before submitting</h2><p>Our assistance fee is separate from government or official charges. You review the applicable amounts before payment.</p></div><div className="home-fee-card"><span>Applicable Assistance Fee</span><dl><div><dt>Standard fee</dt><dd>₹{homepageFee}</dd></div><div><dt>Government / Official Fee</dt><dd>To be confirmed</dd></div></dl></div></section>
    <section className="home-cta"><div><span className="eyebrow light">Everything in one place</span><h2>Jobs, scholarships, services and request tracking—made easier</h2></div><Link className="btn btn-primary light-btn" to="/#service-search">Search now</Link></section>
  </div>
}
