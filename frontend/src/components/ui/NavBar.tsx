import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import logo from '../../assets/logo.jpg'
import { getSession } from '../../services/session'
import { logout, warmAuthServer } from '../../services/auth'
import '../../styles/brand-logo-circle.css'

const preloadJobs=()=>{import('../../pages/Jobs')}
const preloadScholarships=()=>{import('../../pages/Scholarships')}
const preloadLogin=()=>{void warmAuthServer();import('../../pages/Login')}
const preloadAdminLogin=()=>{void warmAuthServer();import('../admin/AdminLogin')}
const preloadRegister=()=>{void warmAuthServer();import('../../pages/Register')}
const preloadDashboard=()=>{import('../../pages/MyOrders')}

export default function NavBar(){
  const [open,setOpen] = useState(false)
  const [session,setSession] = useState(getSession())
  const loc = useLocation()
  const nav = useNavigate()
  const isActive = (p:string) => loc.pathname.startsWith(p)

  useEffect(() => { setSession(getSession()); setOpen(false) }, [loc.pathname, loc.search, loc.hash])
  useEffect(() => { const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') setOpen(false) }; window.addEventListener('keydown', closeOnEscape); return () => window.removeEventListener('keydown', closeOnEscape) }, [])
  useEffect(() => { if (!open) return; const previousOverflow = document.body.style.overflow; document.body.style.overflow = 'hidden'; return () => { document.body.style.overflow = previousOverflow } }, [open])

  const doLogout = () => { logout(); setSession(null); setOpen(false); nav('/') }
  const authenticated = !!session
  const admin = !!session?.is_admin
  const trackTarget = authenticated && !admin ? '/my-orders#track' : `/login?returnTo=${encodeURIComponent('/my-orders#track')}`

  return <header className="site-header">
    <div className="container site-header-inner">
      <Link to={admin ? '/admin/dashboard' : '/'} className="brand-lockup" aria-label="Public Online Service Provider home"><img src={logo} alt="Public Online Service Provider logo" className="brand-mark" /><span><strong className="brand">Public Online Service Provider</strong><small>{admin ? 'Administration portal' : 'Simple. Secure. Citizen-focused.'}</small></span></Link>
      <nav className="main-nav" aria-label="Primary navigation">
        <Link className={loc.pathname==='/'&&!loc.hash?'active':''} to="/">Home</Link>
        <Link className={isActive('/certificates')?'active':''} to="/certificates">MeeSeva Certificates</Link>
        <Link className={isActive('/jobs')?'active':''} to="/jobs" onMouseEnter={preloadJobs} onFocus={preloadJobs}>Jobs</Link>
        <Link className={isActive('/scholarships')?'active':''} to="/scholarships" onMouseEnter={preloadScholarships} onFocus={preloadScholarships}>Scholarships</Link>
        <Link className={isActive('/government-services')?'active':''} to="/government-services">Services</Link>
        {!admin&&<Link to={trackTarget} onMouseEnter={authenticated?preloadDashboard:preloadLogin} onFocus={authenticated?preloadDashboard:preloadLogin}>Track Request</Link>}
        <Link className={isActive('/contact')?'active':''} to="/contact">Help</Link>
      </nav>
      <div className="header-actions">
        <Link className="header-search" to="/#service-search" aria-label="Search services"><svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.2 4.2"/></svg><span>Search</span></Link>
        {!authenticated&&<Link className="header-link" to="/login" onMouseEnter={preloadLogin} onFocus={preloadLogin}>Client Login</Link>}
        {!admin&&<Link className="header-link" to="/admin/login" onMouseEnter={preloadAdminLogin} onFocus={preloadAdminLogin}>Admin Login</Link>}
        {!authenticated&&<Link className="header-signup" to="/register" onMouseEnter={preloadRegister} onFocus={preloadRegister}>Register</Link>}
        {authenticated&&!admin&&<><Link className="header-link" to="/my-orders" onMouseEnter={preloadDashboard} onFocus={preloadDashboard}>Dashboard</Link><Link className="header-signup" to="/account-settings">My Account</Link><button className="header-link" type="button" onClick={doLogout}>Logout</button></>}
        {authenticated&&admin&&<><Link className="header-link" to="/admin/dashboard">Dashboard</Link><Link className="header-signup" to="/admin/orders">Applications</Link><button className="header-link" type="button" onClick={doLogout}>Logout</button></>}
        <button className="mobile-menu-btn" type="button" onClick={()=>setOpen(true)} aria-label="Open navigation menu" aria-expanded={open} aria-controls="mobile-navigation"><span aria-hidden="true">☰</span></button>
      </div>
    </div>
    {open&&<><button className="mobile-drawer-backdrop" type="button" onClick={()=>setOpen(false)} aria-label="Close navigation menu"/><nav id="mobile-navigation" className="mobile-drawer" aria-label="Mobile navigation"><div className="mobile-drawer-header"><div><strong>Menu</strong><small>Quick access</small></div><button type="button" onClick={()=>setOpen(false)} aria-label="Close navigation menu">×</button></div><div className="mobile-drawer-inner">
      <section className="mobile-drawer-section"><strong>Top options</strong><div className="mobile-drawer-links"><Link to="/">Home</Link><Link to="/certificates">MeeSeva Certificates</Link><Link to="/jobs" onMouseEnter={preloadJobs}>Jobs</Link><Link to="/scholarships" onMouseEnter={preloadScholarships}>Scholarships</Link><Link to="/government-services">Services</Link><Link to="/#service-search">Search Services</Link>{!admin&&<Link to={trackTarget} onMouseEnter={authenticated?preloadDashboard:preloadLogin}>{authenticated?'Track My Request':'Client Login to Track Request'}</Link>}</div></section>
      <section className="mobile-drawer-section"><strong>Account</strong><div className="mobile-drawer-links">{authenticated ? (admin ? <><Link to="/admin/dashboard">Dashboard</Link><Link to="/admin/orders">Applications</Link><Link to="/admin/messages">Client Messages</Link><Link to="/admin/services">Services & Fees</Link><button type="button" onClick={doLogout}>Logout</button></> : <><Link to="/my-orders">Dashboard</Link><Link to="/account-settings">My Account</Link><Link to="/messages">Messages</Link><Link to="/admin/login" onMouseEnter={preloadAdminLogin}>Admin Login</Link><button type="button" onClick={doLogout}>Logout</button></>) : <><Link className="drawer-primary-action" to="/login" onMouseEnter={preloadLogin}>Client Login</Link><Link to="/admin/login" onMouseEnter={preloadAdminLogin}>Admin Login</Link><Link className="drawer-register-action" to="/register" onMouseEnter={preloadRegister}>Create Account</Link></>}</div></section>
      <section className="mobile-drawer-section"><strong>Services & information</strong><div className="mobile-drawer-links"><Link to="/schemes">Schemes</Link><Link to="/about">About</Link><Link to="/contact">Contact & Help</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></div></section>
    </div></nav></>}
  </header>
}
