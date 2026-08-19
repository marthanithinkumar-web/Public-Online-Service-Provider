import React from 'react'
import { Routes, Route, Link, useNavigate, useLocation } from 'react-router-dom'
import Home from './pages/Home'
import ServiceDetail from './pages/ServiceDetail'
import Login from './pages/Login'
import AdminLogin from './components/admin/AdminLogin'
import AdminPanel from './components/admin/AdminPanel'
import Register from './pages/Register'
import MyOrders from './pages/MyOrders'
import AccountSettings from './pages/AccountSettings'
import RequestReset from './pages/RequestReset'
import ResetPassword from './pages/ResetPassword'
import { getToken, clearToken } from './services/localStorage'
import Category from './pages/Category'
import SubmitGrievance from './pages/SubmitGrievance'
import SubmitReview from './pages/SubmitReview'
import About from './pages/About'
import Contact from './pages/Contact'
import PrivacyPolicy from './pages/PrivacyPolicy'
import Terms from './pages/Terms'
import Disclaimer from './pages/Disclaimer'
import { PROVIDER } from './services/config'
import logo from './assets/logo.svg'

export default function App(){
  const nav = useNavigate(); const location = useLocation(); const token = getToken(); const isAdmin = location.pathname.startsWith('/admin')
  const doLogout=()=>{clearToken();nav('/login')}
  const isClientArea=['/my-orders','/account-settings','/submit-grievance','/submit-review'].some(p=>location.pathname.startsWith(p))
  return <div className="app-shell">
    <header className={`site-header ${isAdmin?'admin-header':''}`}>
      <div className="container site-header-inner">
        <Link to="/" className="brand-lockup" aria-label="Public Online Service Provider home"><img src={logo} alt="Public Online Service Provider logo" className="brand-mark"/><span><strong className="brand">Public Online Service Provider</strong><small>Simple. Secure. Citizen-focused.</small></span></Link>
        <nav className="main-nav" aria-label="Primary navigation"><Link className={location.pathname.startsWith('/jobs')?'active':''} to="/jobs">Jobs</Link><Link className={location.pathname.startsWith('/scholarships')?'active':''} to="/scholarships">Scholarships</Link><Link className={location.pathname.startsWith('/meeseva')?'active':''} to="/meeseva">MeeSeva</Link><Link className={location.pathname.startsWith('/certificates')?'active':''} to="/certificates">Certificates</Link><Link className={location.pathname.startsWith('/schemes')?'active':''} to="/schemes">Schemes</Link></nav>
        <div className="header-actions">{token?<><Link className={isClientArea?'header-account active':''} to="/my-orders">My Workspace</Link><Link className="header-account" to="/account-settings">Account</Link><button className="header-logout" onClick={doLogout}>Logout</button></>:<><Link className="header-link" to="/login">Login</Link><Link className="header-signup" to="/register">Get Started</Link></>}</div>
      </div>
      <div className="container provider-strip"><span>{PROVIDER.name}</span><span><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></span></div>
    </header>
    <main className="container page-content"><Routes><Route path="/" element={<Home/>}/><Route path="/service/:id" element={<ServiceDetail/>}/><Route path="/jobs" element={<Category/>}/><Route path="/scholarships" element={<Category/>}/><Route path="/meeseva" element={<Category/>}/><Route path="/certificates" element={<Category/>}/><Route path="/schemes" element={<Category/>}/><Route path="/about" element={<About/>}/><Route path="/contact" element={<Contact/>}/><Route path="/privacy" element={<PrivacyPolicy/>}/><Route path="/terms" element={<Terms/>}/><Route path="/disclaimer" element={<Disclaimer/>}/><Route path="/login" element={<Login/>}/><Route path="/register" element={<Register/>}/><Route path="/request-reset" element={<RequestReset/>}/><Route path="/reset-password" element={<ResetPassword/>}/><Route path="/my-orders" element={<MyOrders/>}/><Route path="/account-settings" element={<AccountSettings/>}/><Route path="/submit-grievance" element={<SubmitGrievance/>}/><Route path="/submit-review" element={<SubmitReview/>}/><Route path="/admin/login" element={<AdminLogin/>}/><Route path="/admin/*" element={<AdminPanel/>}/></Routes></main>
    <footer className="site-footer"><div className="container footer-grid"><div><Link to="/" className="brand-lockup footer-lockup"><span className="brand-mark">P</span><span><strong className="brand footer-brand">Public Online Service Provider</strong><small>Simple. Secure. Citizen-focused.</small></span></Link><p className="footer-text">Helping citizens access essential government and public assistance services with clarity, privacy, and trusted support.</p></div><div><h4>Explore</h4><div className="footer-links"><Link to="/jobs">Jobs</Link><Link to="/scholarships">Scholarships</Link><Link to="/certificates">Certificates</Link><Link to="/schemes">Government Schemes</Link></div></div><div><h4>Company</h4><div className="footer-links"><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link to="/privacy">Privacy</Link><Link to="/terms">Terms</Link><Link to="/disclaimer">Disclaimer</Link><Link to="/admin/login">Admin Portal</Link></div></div><div><h4>Contact</h4><div className="footer-links"><a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`tel:${PROVIDER.phone2}`}>{PROVIDER.phone2}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a><span>{PROVIDER.name}</span></div></div></div><div className="container footer-bottom"><span>© 2026 Public Online Service Provider</span><span>Independent assistance platform · Not a government department</span></div></footer>
  </div>
}
