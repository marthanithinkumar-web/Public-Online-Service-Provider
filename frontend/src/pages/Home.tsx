import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import LatestJobs from '../components/jobs/LatestJobs'
import {fetchServiceCatalog,isHomepageHighlightEligible,readCachedServices,servicePath,slugifyServiceName} from '../services/serviceCatalog'
import {fetchScholarships,Scholarship,scholarshipPath} from '../services/scholarships'
import '../styles/home-modern.css'
import '../styles/home-final-alignment.css'
import '../styles/home-redesign.css'

const serviceTerms=['bank account seeding','dbt assistance','caste','income','residence','aadhaar','pan','voter','ration','birth','death','driving','vehicle','passport','land','meeseva','education','legal','health','welfare','labour']
const paymentTerms=['recharge','bill payment','electricity','dth','broadband','water bill','gas bill','fastag']
function paymentDisplayName(value:string){return String(value||'').replace(/^\s*(?:apply(?:\s+for)?|application(?:\s+for)?|request(?:\s+for)?|pay)\s+/i,'').trim()}

export default function Home(){
 const [catalog,setCatalog]=useState<any[]>(()=>readCachedServices(true));const [scholarships,setScholarships]=useState<Scholarship[]>([])
 useEffect(()=>{let a=true;fetchServiceCatalog().then(x=>{if(a)setCatalog(x)}).catch(()=>{});return()=>{a=false}},[])
 useEffect(()=>{let a=true;fetchScholarships().then(x=>{if(a)setScholarships((x.items||[]).slice(0,4))}).catch(()=>{});return()=>{a=false}},[])
 useEffect(()=>{const preload=()=>{import('./ServiceDetail');import('./ServiceDirectory');import('./RechargeBillRequest');import('./Login');import('./Jobs');import('./Scholarships')};const idle=(window as any).requestIdleCallback;const h=idle?idle(preload,{timeout:2500}):window.setTimeout(preload,1200);return()=>idle?(window as any).cancelIdleCallback?.(h):window.clearTimeout(h)},[])
 const browse=useMemo(()=>{const eligible=catalog.filter(isHomepageHighlightEligible).filter(s=>!`${s.name} ${s.keywords||''}`.toLowerCase().includes('fraud complaint')),out:any[]=[];serviceTerms.forEach(t=>{const m=eligible.find(s=>!out.includes(s)&&`${s.name} ${s.category||''} ${s.keywords||''}`.toLowerCase().includes(t));if(m)out.push(m)});eligible.forEach(s=>{if(out.length<12&&!out.includes(s))out.push(s)});return out.slice(0,12)},[catalog])
 const payments=useMemo(()=>catalog.filter(s=>paymentTerms.some(t=>`${s.name} ${s.category||''} ${s.keywords||''}`.toLowerCase().includes(t))).slice(0,4),[catalog])
 const icon=(name:string)=>{const n=name.toLowerCase();if(n.includes('seeding')||n.includes('dbt'))return'↔';if(n.includes('aadhaar'))return'◎';if(n.includes('vehicle')||n.includes('driving'))return'▰';if(n.includes('passport')||n.includes('pan')||n.includes('voter'))return'▣';if(n.includes('land'))return'⌂';if(n.includes('health'))return'♥';if(n.includes('education'))return'◆';return'▤'}
 const paymentPath=(service:any)=>`/recharge-bills/${encodeURIComponent(service.slug||slugifyServiceName(service.name))}`
 return <div className="world-home">
  <section className="world-hero">
   <div className="world-hero-copy">
    <span className="world-kicker">PUBLIC ONLINE SERVICE PROVIDER</span>
    <h1>Find the right service.<br/><em>Finish it with confidence.</em></h1>
    <p>Search government services, certificates, jobs, scholarships and bill payments from one clear starting point.</p>
    <SearchPanel variant="hero"/>
    <div className="hero-confidence" aria-label="Platform highlights"><span>✓ Clear requirements</span><span>✓ Secure website flow</span><span>✓ Request tracking</span></div>
   </div>
   <aside className="world-hero-side" aria-label="How to get started">
    <span className="side-kicker">START HERE</span>
    <h2>From search to completion in a few clear steps.</h2>
    <div className="hero-step"><b>01</b><div><strong>Search</strong><span>Find the exact service or opportunity you need.</span></div></div>
    <div className="hero-step"><b>02</b><div><strong>Review</strong><span>Check requirements, fees and next steps before you continue.</span></div></div>
    <div className="hero-step"><b>03</b><div><strong>Submit & track</strong><span>Send your request securely and follow its progress online.</span></div></div>
    <Link className="hero-side-link" to="/government-services">Browse all services →</Link>
   </aside>
  </section>

  <section className="quick-access-section" aria-labelledby="quick-access-title">
   <div className="section-heading-row"><div><span className="section-kicker">QUICK ACCESS</span><h2 id="quick-access-title">What do you want to do today?</h2></div><p>Choose a common starting point. You can always search for something more specific above.</p></div>
   <div className="world-primary">
    <Link to="/certificates"><i>▤</i><div><span className="quick-label">SERVICES</span><h3>MeeSeva & Certificates</h3><p>Income, caste, residence, birth and other certificate assistance.</p></div><b>›</b></Link>
    <Link to="/jobs"><i>▣</i><div><span className="quick-label">OPPORTUNITIES</span><h3>Jobs</h3><p>Browse current government and private job opportunities.</p></div><b>›</b></Link>
    <Link to="/scholarships"><i>◆</i><div><span className="quick-label">EDUCATION</span><h3>Scholarships</h3><p>Discover current scholarship opportunities and eligibility details.</p></div><b>›</b></Link>
    <Link to="/recharge-bills"><i>₹</i><div><span className="quick-label">PAYMENTS</span><h3>Recharge & Bills</h3><p>Start a guided recharge or bill-payment request.</p></div><b>›</b></Link>
   </div>
  </section>

  <section className="world-section service-browser" id="browse-services">
   <header><div><span className="section-kicker">POPULAR SERVICES</span><h2>Frequently needed government services</h2><p>Open a service to see what it is for, what you need and how to proceed.</p></div><Link to="/government-services">View all services →</Link></header>
   <div className="service-icon-grid">{browse.map(s=><Link key={s.id} to={servicePath(s)}><i>{icon(s.name)}</i><span>{s.name}</span></Link>)}</div>
  </section>

  <section className="process-section" aria-labelledby="process-title">
   <div className="section-heading-row compact"><div><span className="section-kicker">HOW IT WORKS</span><h2 id="process-title">A simple path from question to completed request</h2></div></div>
   <div className="process-grid">
    <div><b>1</b><h3>Find the service</h3><p>Use search or browse categories to reach the right page quickly.</p></div>
    <div><b>2</b><h3>Check before you start</h3><p>See the purpose, requirements, fee information and expected next steps.</p></div>
    <div><b>3</b><h3>Submit securely</h3><p>Continue through the website for forms, documents and payments where applicable.</p></div>
    <div><b>4</b><h3>Track progress</h3><p>Use your request page to follow status updates and contact support when needed.</p></div>
   </div>
  </section>

  <section className="world-information-grid opportunity-grid">
   <div className="world-panel jobs-panel"><header><div><span className="section-kicker">LATEST</span><h2>Government & Private Jobs</h2><p>Current opportunities collected from priority official and trusted sources.</p></div><Link to="/jobs">View all jobs →</Link></header><LatestJobs maxItems={2}/></div>
   <div className="world-panel scholarship-panel"><header><div><span className="section-kicker">LATEST</span><h2>Scholarships</h2><p>Recent scholarship opportunities with provider information and application details.</p></div><Link to="/scholarships">View all scholarships →</Link></header><div className="compact-list">{scholarships.length?scholarships.map(s=><Link key={s.id} to={scholarshipPath(s)}><i>◆</i><div><b>{s.title}</b><span>{s.provider}</span></div><strong>Open</strong></Link>):<p>Scholarships are loading…</p>}</div></div>
  </section>

  <section className="payments-support-section">
   <div className="world-panel payments-panel" id="payments"><header><div><span className="section-kicker">PAYMENTS</span><h2>Recharge & bill payments</h2><p>Choose a payment type and continue through the guided request flow.</p></div><Link to="/recharge-bills">See all payment options →</Link></header><div className="payment-grid">{payments.length?payments.map(s=><Link key={s.id} to={paymentPath(s)}><i>₹</i><span>{paymentDisplayName(s.name)}</span></Link>):<><Link to="/recharge-bills"><i>▣</i><span>Mobile Recharge</span></Link><Link to="/recharge-bills"><i>⚡</i><span>Electricity Bill</span></Link><Link to="/recharge-bills"><i>◉</i><span>DTH Recharge</span></Link><Link to="/recharge-bills"><i>▤</i><span>Other Bills</span></Link></>}</div></div>
   <aside className="support-panel"><span className="section-kicker">NEED HELP?</span><h2>Not sure which service to choose?</h2><p>Contact support with your question. For your safety, never send passwords, OTPs, PINs, CVV details or banking credentials in chat.</p><div className="support-actions"><Link className="primary-action" to="/contact">Contact support</Link><Link to="/government-services">Browse services</Link></div></aside>
  </section>

  <section className="trust-strip" aria-label="Why use Public Online Service Provider"><div><b>✓</b><span><strong>Clear guidance</strong>Know what to do next</span></div><div><b>⌁</b><span><strong>One place</strong>Services and opportunities together</span></div><div><b>◎</b><span><strong>Mobile friendly</strong>Designed for everyday use</span></div><div><b>♥</b><span><strong>Support available</strong>Help when you need it</span></div></section>

  <section className="world-cta"><div><span>PUBLIC ONLINE SERVICE PROVIDER</span><h2>Start with a search. Continue with a clear next step.</h2><p>A product of MNK Technologies</p></div><Link to="/government-services">Explore services →</Link></section>
 </div>
}
