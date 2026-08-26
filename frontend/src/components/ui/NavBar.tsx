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
          <img src={logo} alt="logo" className="brand-mark" />
          <span><strong className="brand">Public Online Service Provider</strong><small>{admin ? 'Administration portal' : 'Simple. Secure. Citizen-focused.'}</small></span>
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
          <button className="mobile-menu-btn" type="button" onClick={()=>setOpen(value=>!value)} aria-label={open ? 'Close navigation menu' : 'Open navigation menu'} aria-expanded={open} aria-controls="mobile-navigation"><span aria-hidden="true">{open?'×':'☰'}</span><span className="mobile-menu-label">{open?'Close':'Menu'}</span></button>
        </div>
      </div>
      <div className="container provider-strip"><span>{PROVIDER.name}</span><span><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></span></div>
      <nav className="container mobile-primary-actions" aria-label="Account shortcuts">
        {!authenticated&&<><Link className="mobile-login-shortcut" to="/login">Client Login</Link><Link className="mobile-register-shortcut" to="/register">Register</Link></>}
        {authenticated&&!admin&&<><Link to="/my-orders">Dashboard</Link><Link to="/account-settings">My Account</Link></>}
        {authenticated&&admin&&<><Link to="/admin/dashboard">Admin Dashboard</Link><Link to="/admin/orders">Requests</Link></>}
      </nav>
      {open && <nav id="mobile-navigation" className="mobile-drawer" aria-label="Mobile navigation"><div className="container mobile-drawer-inner">
        <section className="mobile-drawer-section"><strong>Account</strong><div className="mobile-drawer-links">{authenticated ? (admin ? <><Link to="/admin/dashboard">Dashboard</Link><Link to="/admin/orders">Requests</Link><Link to="/admin/services">Services</Link><Link to="/admin/users">Clients</Link><button type="button" onClick={doLogout}>Logout</button></> : <><Link to="/my-orders">Dashboard</Link><Link to="/my-orders#applications">My Applications</Link><Link to="/account-settings">My Account</Link><button type="button" onClick={doLogout}>Logout</button></>) : <><Link to="/login">Client Login</Link><Link to="/register">Register</Link><Link to="/admin/login">Admin Login</Link></>}</div></section>
        <section className="mobile-drawer-section"><strong>Explore services</strong><div className="mobile-drawer-links"><Link to="/jobs">Jobs</Link><Link to="/scholarships">Scholarships</Link><Link to="/meeseva">MeeSeva</Link><Link to="/certificates">Certificates</Link><Link to="/schemes">Schemes</Link><Link to="/about">About</Link><Link to="/contact">Contact</Link></div></section>
      </div></nav>}
    </header>
  )
}
