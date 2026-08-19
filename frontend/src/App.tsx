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
import NavBar from './components/ui/NavBar'
import Footer from './components/ui/Footer'

export default function App(){
  const nav = useNavigate(); const location = useLocation(); const token = getToken(); const isAdmin = location.pathname.startsWith('/admin')
  const doLogout=()=>{clearToken();nav('/login')}
  const isClientArea=['/my-orders','/account-settings','/submit-grievance','/submit-review'].some(p=>location.pathname.startsWith(p))
  return (
    <div className="app-shell">
      <NavBar />
      <main className="container page-content">
        <Routes>
          <Route path="/" element={<Home/>}/>
          <Route path="/service/:id" element={<ServiceDetail/>}/>
          <Route path="/jobs" element={<Category/>}/>
          <Route path="/scholarships" element={<Category/>}/>
          <Route path="/meeseva" element={<Category/>}/>
          <Route path="/certificates" element={<Category/>}/>
          <Route path="/schemes" element={<Category/>}/>
          <Route path="/about" element={<About/>}/>
          <Route path="/contact" element={<Contact/>}/>
          <Route path="/privacy" element={<PrivacyPolicy/>}/>
          <Route path="/terms" element={<Terms/>}/>
          <Route path="/disclaimer" element={<Disclaimer/>}/>
          <Route path="/login" element={<Login/>}/>
          <Route path="/register" element={<Register/>}/>
          <Route path="/request-reset" element={<RequestReset/>}/>
          <Route path="/reset-password" element={<ResetPassword/>}/>
          <Route path="/my-orders" element={<MyOrders/>}/>
          <Route path="/account-settings" element={<AccountSettings/>}/>
          <Route path="/submit-grievance" element={<SubmitGrievance/>}/>
          <Route path="/submit-review" element={<SubmitReview/>}/>
          <Route path="/admin/login" element={<AdminLogin/>}/>
          <Route path="/admin/*" element={<AdminPanel/>}/>
        </Routes>
      </main>
      <Footer />
    </div>
  )

}
