import React, { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import logo from '../../assets/logo.svg'
import { PROVIDER } from '../../services/config'

export default function NavBar(){
  const [open,setOpen] = useState(false)
  const loc = useLocation()
  const isActive = (p:string) => loc.pathname.startsWith(p)
  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link to="/" className="brand-lockup" aria-label="Public Online Service Provider home">
          <img src={logo} alt="logo" className="brand-mark" />
          <span><strong className="brand">Public Online Service Provider</strong><small>Simple. Secure. Citizen-focused.</small></span>
        </Link>
        <nav className="main-nav" aria-label="Primary navigation">
          <Link className={isActive('/jobs')? 'active':''} to="/jobs">Jobs</Link>
          <Link className={isActive('/scholarships')? 'active':''} to="/scholarships">Scholarships</Link>
          <Link className={isActive('/meeseva')? 'active':''} to="/meeseva">MeeSeva</Link>
          <Link className={isActive('/certificates')? 'active':''} to="/certificates">Certificates</Link>
          <Link className={isActive('/schemes')? 'active':''} to="/schemes">Schemes</Link>
          <Link className={isActive('/about')? 'active':''} to="/about">About</Link>
          <Link className={isActive('/contact')? 'active':''} to="/contact">Contact</Link>
        </nav>
        <div className="header-actions">
          <Link className="header-link" to="/admin/login">Admin Portal</Link>
          <Link className="header-link" to="/login">Login</Link>
          <Link className="header-signup" to="/register">Get Started</Link>
          <button className="mobile-menu-btn" onClick={()=>setOpen(!open)} aria-label="Toggle menu">☰</button>
        </div>
      </div>
      <div className="container provider-strip"><span>{PROVIDER.name}</span><span><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></span></div>
      {open && <div className="mobile-drawer"><div className="container mobile-drawer-inner"><Link to="/jobs">Jobs</Link><Link to="/scholarships">Scholarships</Link><Link to="/meeseva">MeeSeva</Link><Link to="/certificates">Certificates</Link><Link to="/schemes">Schemes</Link><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/login">Login</Link><Link to="/register">Get Started</Link></div></div>}
    </header>
  )
}
