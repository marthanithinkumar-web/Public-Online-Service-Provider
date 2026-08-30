import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import logo from '../../assets/logo.svg'
import { PROVIDER } from '../../services/config'
import { getSession } from '../../services/session'
import { logout } from '../../services/auth'

export default function NavBar(){
  const [open,setOpen] = useState(false)
  const [session,setSession] = useState(getSession())
  const loc = useLocation()
  const nav = useNavigate()
  const isActive = (p:string) => loc.pathname.startsWith(p)

  useEffect(() => {
    setSession(getSession())
    setOpen(false)
  }, [loc.pathname, loc.search, loc.hash])

  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [])

  useEffect(() => {
    if (!open) return
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = previousOverflow }
  }, [open])

  const doLogout = () => {
    logout()
    setSession(null)
    setOpen(false)
    nav('/')
  }

  const authenticated = !!session
  const admin = !!session?.is_admin

  return (
    <header className="site-header">
      <div className="container site-header-inner">
        <Link to={admin ? '/admin/dashboard' : '/'} className="brand-lockup" aria-label="Public Online Service Provider home">
          <img src={logo} alt="" className="brand-mark" />
          <span><strong className="brand">Public Online Service Provider</strong><small>{admin ? 'Administration portal' : 'Simple. Secure. Citizen-focused.'}</small></span>
        </Link>
        <nav className="main-nav" aria-label="Primary navigation">
          <Link className={loc.pathname==='/'&&!loc.hash? 'active':''} to="/">Home</Link>
          <Link to="/#services">Services</Link>
          <Link to="/login?returnTo=%2Fmy-orders">Track Request</Link>
          <Link to="/#how-it-works">How It Works</Link>
          <Link to="/#help">Help</Link>
          <Link className={isActive('/contact')? 'active':''} to="/contact">Contact</Link>
        </nav>
        <div className="header-actions">
          <Link className="header-search" to="/#service-search" aria-label="Search services"><svg aria-hidden="true" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.2 4.2"/></svg><span>Search</span></Link>
          {!authenticated && <>
            <Link className="header-admin" to="/admin/login">Admin Login</Link>
            <Link className="header-link" to="/login">Client Login</Link>
            <Link className="header-signup" to="/register">Register</Link>
          </>}
          {authenticated && !admin && <>
            <Link className="header-link" to="/my-orders">Dashboard</Link>
            <Link className="header-link" to="/my-orders#applications">My Applications</Link>
            <Link className="header-signup" to="/account-settings">My Account</Link>
            <button className="header-link" type="button" onClick={doLogout}>Logout</button>
          </>}
          {authenticated && admin && <>
            <Link className="header-link" to="/admin/dashboard">Dashboard</Link>
            <Link className="header-signup" to="/admin/orders">Requests</Link>
            <button className="header-link" type="button" onClick={doLogout}>Logout</button>
          </>}
          <button className="mobile-menu-btn" type="button" onClick={()=>setOpen(true)} aria-label="Open navigation menu" aria-expanded={open} aria-controls="mobile-navigation"><span aria-hidden="true">☰</span></button>
        </div>
      </div>
      <div className="container provider-strip"><span>{PROVIDER.name}</span><span><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></span></div>
      {open&&<><button className="mobile-drawer-backdrop" type="button" onClick={()=>setOpen(false)} aria-label="Close navigation menu"/><nav id="mobile-navigation" className="mobile-drawer" aria-label="Mobile navigation"><div className="mobile-drawer-header"><div><strong>Menu</strong><small>Public Online Service Provider</small></div><button type="button" onClick={()=>setOpen(false)} aria-label="Close navigation menu">×</button></div><div className="mobile-drawer-inner">
        <section className="mobile-drawer-section"><strong>Account</strong><div className="mobile-drawer-links">{authenticated ? (admin ? <><Link to="/admin/dashboard">Dashboard</Link><Link to="/admin/orders">Requests</Link><Link to="/admin/messages">Client Messages</Link><Link to="/admin/services">Services</Link><Link to="/admin/users">Clients</Link><button type="button" onClick={doLogout}>Logout</button></> : <><Link to="/my-orders">Dashboard</Link><Link to="/my-orders#applications">My Applications</Link><Link to="/my-orders#track">Track My Request</Link><Link to="/account-settings">My Account</Link><button type="button" onClick={doLogout}>Logout</button></>) : <><Link className="drawer-primary-action" to="/login">Client Login</Link><Link className="drawer-register-action" to="/register">Create Account</Link><Link to="/admin/login">Admin Login</Link></>}</div></section>
        <section className="mobile-drawer-section"><strong>Find a service</strong><div className="mobile-drawer-links"><Link to="/#service-search">Search Services</Link><Link to="/jobs">Jobs</Link><Link to="/scholarships">Scholarships</Link><Link to="/meeseva">MeeSeva</Link><Link to="/certificates">Certificates</Link><Link to="/schemes">Schemes</Link></div></section>
        <section className="mobile-drawer-section"><strong>Information & support</strong><div className="mobile-drawer-links"><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link></div></section>
      </div></nav></>}
    </header>
  )
}
