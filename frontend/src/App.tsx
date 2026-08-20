import React from 'react'
import {Routes,Route,Navigate,useLocation} from 'react-router-dom'
import Home from './pages/Home'
import ServiceDetail from './pages/ServiceDetail'
import Login from './pages/Login'
import AdminLogin from './components/admin/AdminLogin'
import AdminPanel from './components/admin/AdminPanel'
import Register from './pages/Register'
import MyOrders from './pages/MyOrders'
import OrderDetail from './pages/OrderDetail'
import AccountSettings from './pages/AccountSettings'
import RequestReset from './pages/RequestReset'
import ResetPassword from './pages/ResetPassword'
import Category from './pages/Category'
import SubmitGrievance from './pages/SubmitGrievance'
import SubmitReview from './pages/SubmitReview'
import About from './pages/About'
import Contact from './pages/Contact'
import PrivacyPolicy from './pages/PrivacyPolicy'
import Terms from './pages/Terms'
import Disclaimer from './pages/Disclaimer'
import NavBar from './components/ui/NavBar'
import Footer from './components/ui/Footer'
import {getSession} from './services/session'

function safeReturnTo(value:string|null){
  if(!value)return null
  try{
    const decoded=decodeURIComponent(value)
    return decoded.startsWith('/')&&!decoded.startsWith('//')&&!decoded.startsWith('/login')&&!decoded.startsWith('/register')&&!decoded.startsWith('/admin/login')?decoded:null
  }catch{return null}
}

function AuthRedirect({children}:{children:React.ReactNode}){
  const location=useLocation()
  const session=getSession()
  if(!session)return <>{children}</>
  const returnTo=safeReturnTo(new URLSearchParams(location.search).get('returnTo'))
  if(returnTo)return <Navigate to={returnTo} replace/>
  return <Navigate to={session.is_admin?'/admin/dashboard':'/my-orders'} replace/>
}
function ClientRoute({children}:{children:React.ReactNode}){const session=getSession();if(!session)return <Navigate to="/login" replace/>;if(session.is_admin)return <Navigate to="/admin/dashboard" replace/>;return <>{children}</>}
function AdminRoute({children}:{children:React.ReactNode}){const session=getSession();if(!session)return <Navigate to="/admin/login" replace/>;if(!session.is_admin)return <Navigate to="/my-orders" replace/>;return <>{children}</>}

export default function App(){return <div className="app-shell"><NavBar/><main className="container page-content"><Routes>
 <Route path="/" element={<Home/>}/><Route path="/service/:id" element={<ServiceDetail/>}/><Route path="/jobs" element={<Category/>}/><Route path="/scholarships" element={<Category/>}/><Route path="/meeseva" element={<Category/>}/><Route path="/certificates" element={<Category/>}/><Route path="/schemes" element={<Category/>}/><Route path="/about" element={<About/>}/><Route path="/contact" element={<Contact/>}/><Route path="/privacy" element={<PrivacyPolicy/>}/><Route path="/terms" element={<Terms/>}/><Route path="/disclaimer" element={<Disclaimer/>}/>
 <Route path="/login" element={<AuthRedirect><Login/></AuthRedirect>}/><Route path="/register" element={<AuthRedirect><Register/></AuthRedirect>}/><Route path="/admin/login" element={<AuthRedirect><AdminLogin/></AuthRedirect>}/><Route path="/request-reset" element={<RequestReset/>}/><Route path="/reset-password" element={<ResetPassword/>}/>
 <Route path="/my-orders" element={<ClientRoute><MyOrders/></ClientRoute>}/><Route path="/my-orders/:id" element={<ClientRoute><OrderDetail/></ClientRoute>}/><Route path="/account-settings" element={<ClientRoute><AccountSettings/></ClientRoute>}/><Route path="/submit-grievance" element={<ClientRoute><SubmitGrievance/></ClientRoute>}/><Route path="/submit-review" element={<ClientRoute><SubmitReview/></ClientRoute>}/><Route path="/admin/*" element={<AdminRoute><AdminPanel/></AdminRoute>}/><Route path="*" element={<Navigate to="/" replace/>}/>
 </Routes></main><Footer/></div>}
