import React from 'react'
import { Link } from 'react-router-dom'
import { PROVIDER } from '../../services/config'
import logo from '../../assets/logo.svg'

export default function Footer(){
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <Link to="/" className="brand-lockup footer-lockup"><img src={logo} alt="Public Online Service Provider" className="brand-mark"/><span><strong className="brand footer-brand">Public Online Service Provider</strong><small>Simple. Secure. Citizen-focused.</small></span></Link>
          <p className="footer-text">Private assistance for public-service applications, delivered with clarity, privacy and trusted support.</p>
          <p className="footer-disclaimer">Independent private assistance provider. Not a government department or official government portal.</p>
        </div>
        <div>
          <h4>Explore</h4>
          <div className="footer-links"><Link to="/jobs">Jobs</Link><Link to="/scholarships">Scholarships</Link><Link to="/certificates">Certificates</Link><Link to="/meeseva">MeeSeva Services</Link><Link to="/schemes">Government Schemes</Link></div>
        </div>
        <div>
          <h4>Company</h4>
          <div className="footer-links"><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link><Link to="/disclaimer">Disclaimer</Link><Link to="/admin/login">Admin Portal</Link></div>
        </div>
        <div>
          <h4>Contact</h4>
          <address className="footer-contact"><strong>{PROVIDER.name}</strong><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a><a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a><a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></address>
        </div>
      </div>
      <div className="container footer-bottom"><div className="footer-bottom-inner"><span>© 2026 Public Online Service Provider</span><span>Independent assistance platform · Not a government department</span></div></div>
    </footer>
  )
}
