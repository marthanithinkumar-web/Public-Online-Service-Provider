import React from 'react'
import { Routes, Route, Link, useNavigate } from 'react-router-dom'
import Home from './pages/Home'
import ServiceDetail from './pages/ServiceDetail'
import Login from './pages/Login'
import AdminLogin from './components/admin/AdminLogin'
import AdminPanel from './components/admin/AdminPanel'
import Register from './pages/Register'
import MyOrders from './pages/MyOrders'
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
export default function App(){
  const nav = useNavigate()
  const token = getToken()

  const doLogout = () => { clearToken(); nav('/') }

  return (
    <div>
      <header className="site-header">
        <div className="container" style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
            <div style={{display:'flex',alignItems:'center',gap:16}}>
              <Link to="/" className="brand">Public Online Service Provider</Link>
              <div style={{fontSize:12,color:'#e6f7ff'}}>
                <div>{PROVIDER.name}</div>
                <div><a href={`tel:${PROVIDER.phone}`} style={{color:'#e6f7ff'}}>{PROVIDER.phone}</a> â€¢ <a href={`mailto:${PROVIDER.email}`} style={{color:'#e6f7ff'}}>{PROVIDER.email}</a></div>
              </div>
            </div>
            <nav>
              {token ? (
                <>
                  <Link to="/my-orders" style={{color:'#fff',marginRight:12}}>My Orders</Link>
                  <button onClick={doLogout} style={{background:'transparent',border:'1px solid rgba(255,255,255,0.2)',color:'#fff',padding:'6px 8px',borderRadius:6}}>Logout</button>
                </>
              ) : (
                <>
                  <Link to="/login" style={{color:'#fff',marginRight:12}}>Login</Link>
                  <Link to="/register" style={{color:'#fff',marginRight:12}}>Register</Link>
                  <Link to="/admin/login" style={{color:'#dff7ff',background:'rgba(255,255,255,0.08)',padding:'6px 10px',borderRadius:6,border:'1px solid rgba(255,255,255,0.2)'}}>Admin Login</Link>
                </>
              )}
            </nav>
          </div>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/service/:id" element={<ServiceDetail />} />
                    <Route path="/jobs" element={<Category/>} />
                    <Route path="/scholarships" element={<Category/>} />
                    <Route path="/meeseva" element={<Category/>} />
                    <Route path="/certificates" element={<Category/>} />
                    <Route path="/schemes" element={<Category/>} />
                    <Route path="/about" element={<About/>} />
                    <Route path="/contact" element={<Contact/>} />
                    <Route path="/privacy" element={<PrivacyPolicy/>} />
                    <Route path="/terms" element={<Terms/>} />
                    <Route path="/disclaimer" element={<Disclaimer/>} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/request-reset" element={<RequestReset />} />
                    <Route path="/reset-password" element={<ResetPassword />} />
                    <Route path="/my-orders" element={<MyOrders />} />
                    <Route path="/submit-grievance" element={<SubmitGrievance />} />
                    <Route path="/submit-review" element={<SubmitReview />} />
                    <Route path="/admin/login" element={<AdminLogin />} />
                    <Route path="/admin/*" element={<AdminPanel />} />
        </Routes>
      </main>
      <footer className="site-footer">
        <div className="container footer-grid">
          <div>
            <div className="brand footer-brand">Public Online Service Provider</div>
            <p className="footer-text">Helping citizens access essential government and public assistance services with clarity, privacy, and trusted support.</p>
          </div>
          <div>
            <h4>Quick Links</h4>
            <div className="footer-links">
              <Link to="/about">About</Link>
              <Link to="/contact">Contact</Link>
              <Link to="/privacy">Privacy</Link>
              <Link to="/terms">Terms</Link>
            </div>
          </div>
          <div>
            <h4>Contact</h4>
            <div className="footer-links">
              <a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a>
              <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a>
              <span>{PROVIDER.name}</span>
            </div>
          </div>
        </div>
        <div className="container footer-bottom">
          <span>© 2026 Public Online Service Provider</span>
        </div>
      </footer>
    </div>
  )
}

