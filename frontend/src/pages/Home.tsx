import React from 'react'
import { Link } from 'react-router-dom'
import SearchPanel from '../components/ui/SearchPanel'
import ServicesSection from '../components/ui/ServicesSection'
import WhyChoose from '../components/ui/WhyChoose'
import HowItWorks from '../components/ui/HowItWorks'
import CategoriesSection from '../components/ui/CategoriesSection'

export default function Home(){
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
        <div className="hero-panel"><div className="mini-card"><span className="mini-label">Simple request journey</span><ul><li>Find the right service</li><li>Review requirements and fees</li><li>Submit only necessary details</li><li>Track every important update</li></ul></div><div className="mini-card trust-box"><span className="mini-label">Privacy first</span><p>Your documents and details are handled with care and only used for your requested service.</p></div></div>
      </section>

      <SearchPanel />
      <ServicesSection />
      <WhyChoose />
      <HowItWorks />
      <CategoriesSection />

      <section className="content-section privacy-block"><div className="privacy-copy"><span className="eyebrow">Safety & privacy</span><h2>Your information stays protected.</h2><p>We only request the information needed for your service requirement, keep your data private, and guide you securely through the process. We do not represent a government department and we are committed to privacy-first assistance.</p></div><div className="trust-points"><div>Private document handling</div><div>Secure service request flow</div><div>Clear communication</div></div></section>
      <section className="home-cta"><div><span className="eyebrow light">Need help now?</span><h2>Request assistance and let us guide your application.</h2></div><Link className="btn btn-primary light-btn" to="/register">Request Assistance</Link></section>
    </div>
  )
}
