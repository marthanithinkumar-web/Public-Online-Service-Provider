import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import CategoriesSection from '../components/ui/CategoriesSection'
import LatestJobs from '../components/jobs/LatestJobs'
import {fetchServiceCatalog,isHomepageHighlightEligible,readCachedServices,servicePath} from '../services/serviceCatalog'
import axios from 'axios'
import {apiBase} from '../services/apiBase'

const crucialTerms=['pan','income certificate','scholarship']

export default function Home(){
  const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true))
  const [reviews,setReviews]=useState<any[]>([])
  const [homepageFee,setHomepageFee]=useState<number>(30)
  useEffect(()=>{let active=true;fetchServiceCatalog(true).then(items=>{if(active)setCatalog(items)}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/reviews/public`,{timeout:12000}).then(response=>{if(active)setReviews((response.data||[]).slice(0,6))}).catch(()=>{});return()=>{active=false}},[])
  useEffect(()=>{let active=true;axios.get(`${apiBase}/services/homepage-assistance-fee`,{timeout:12000}).then(response=>{const value=Number(response.data?.price_inr);if(active&&Number.isFinite(value)&&value>=0)setHomepageFee(value)}).catch(()=>{});return()=>{active=false}},[])
  const crucial=useMemo(()=>{const eligible=catalog.filter(isHomepageHighlightEligible);const selected:any[]=[];crucialTerms.forEach(term=>{const match=eligible.find(service=>!selected.includes(service)&&`${service.name} ${service.keywords||''}`.toLowerCase().includes(term));if(match)selected.push(match)});eligible.forEach(service=>{if(selected.length<3&&!selected.includes(service))selected.push(service)});return selected.slice(0,3)},[catalog])
  return <div className="home-page redesigned-home">
    <div className="independent-banner">Independent assistance platform — not a government department or official portal.</div>
    <section className="hero concept-hero"><div className="hero-copy"><span className="eyebrow light">Public services and opportunities</span><h1>Simplifying access to essential services and opportunities</h1><p>Find independent assistance for public-service applications, latest official-source job notices and important resources—all in one place.</p><SearchPanel variant="hero"/><div className="hero-links"><Link className="hero-link-primary" to="/#services">Explore services</Link><Link className="hero-link-track" to="/jobs">Browse latest jobs</Link></div></div><aside className="hero-panel" aria-label="Safety and account access"><div className="hero-safety-card"><span className="safety-shield">✓</span><div><strong>Your security matters</strong><p>Your OTP, PIN, CVV and passwords are never requested.</p></div></div><div className="hero-highlight-grid"><div><strong>{catalog.length||'100+'}</strong><span>Service options</span></div><div><strong>Daily</strong><span>Official job checks</span></div><div><strong>Private</strong><span>Account workspace</span></div><div><strong>24/7</strong><span>Online access</span></div></div><div className="hero-account-actions"><Link to="/register">Create account</Link><Link to="/login">Client login</Link></div></aside></section>
    <LatestJobs/>
    <section className="content-section crucial-services" aria-labelledby="crucial-services-title"><div className="section-header"><div><span className="eyebrow">Frequently needed</span><h2 id="crucial-services-title">Crucial Services</h2></div><Link className="text-link" to="/#service-search">View all services →</Link></div><div className="crucial-service-grid">{crucial.map((service,index)=><Link className="crucial-service-card" to={servicePath(service)} key={service.id}><span className={`crucial-icon tone-${index+1}`} aria-hidden="true">{index===0?'▤':index===1?'▧':'◆'}</span><div><h3>{service.name}</h3><p>{service.description}</p><small>Applicable Assistance Fee ₹{Number(service.price_inr||0)}</small></div><span className="crucial-arrow" aria-hidden="true">›</span></Link>)}</div></section>
    <CategoriesSection/>
    <ServicesSection/>
    {reviews.length>0&&<section className="content-section" aria-labelledby="client-reviews-title"><div className="section-header"><div><span className="eyebrow">Client feedback</span><h2 id="client-reviews-title">Ratings & suggestions</h2></div></div><div className="review-grid">{reviews.map(review=><article className="review-card" key={review.id}><div className="review-stars" aria-label={`${review.rating} out of 5 stars`}>{'★'.repeat(review.rating)}{'☆'.repeat(5-review.rating)}</div><p>{review.comment||'Thank you.'}</p><footer><strong>{review.reviewer}</strong>{review.service&&<span>{review.service}</span>}</footer></article>)}</div></section>}
    <section className="content-section privacy-block simplified-home-fee" id="help"><div className="privacy-copy"><span className="eyebrow">Transparent fees</span><h2>Know the charges before submitting</h2><p>Our assistance fee is shown separately from any government or official charge. You review both before submitting a request.</p></div><div className="home-fee-card"><span>Applicable Assistance Fee</span><dl><div><dt>Standard fee</dt><dd>₹{homepageFee}</dd></div><div><dt>Government / Official Fee</dt><dd>As applicable</dd></div></dl></div></section>
    <section className="home-cta"><div><span className="eyebrow light">Ready when you are</span><h2>Find the right service and track every update</h2></div><Link className="btn btn-primary light-btn" to="/#service-search">Find a service</Link></section>
  </div>
}
