import React,{useEffect} from 'react'
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
import MyGrievances from './pages/MyGrievances'
import SubmitReview from './pages/SubmitReview'
import About from './pages/About'
import Contact from './pages/Contact'
import PrivacyPolicy from './pages/PrivacyPolicy'
import Terms from './pages/Terms'
import Disclaimer from './pages/Disclaimer'
import NavBar from './components/ui/NavBar'
import Footer from './components/ui/Footer'
import {getSession} from './services/session'
import NotFound from './pages/NotFound'

const PUBLIC_TITLES:Record<string,string>={
  '/':'Public Online Service Provider — Public-Service Application Assistance',
  '/jobs':'Government Job Application Assistance', '/scholarships':'Scholarship Application Assistance',
  '/meeseva':'MeeSeva and Public Service Assistance', '/certificates':'Certificate Application Assistance',
  '/schemes':'Government Scheme Application Assistance', '/about':'About Public Online Service Provider',
  '/contact':'Contact Public Online Service Provider', '/privacy':'Privacy Policy', '/terms':'Terms and Conditions',
  '/disclaimer':'Private Provider Disclaimer', '/login':'Client Login', '/register':'Create Client Account',
  '/request-reset':'Password Recovery', '/reset-password':'Reset Password',
}
function RouteMetadata(){
  const location=useLocation()
  useEffect(()=>{
    const path=location.pathname
    document.title=PUBLIC_TITLES[path]||(path.startsWith('/service/')?'Service Details — Public Online Service Provider':path.startsWith('/admin')?'Admin Portal — Public Online Service Provider':path.startsWith('/my-orders')?'My Applications — Public Online Service Provider':'Public Online Service Provider')
    const privatePage=path.startsWith('/admin')||path.startsWith('/my-orders')||path.startsWith('/account-settings')||path.startsWith('/grievances')||path.startsWith('/submit-')||path.startsWith('/reset-password')
    let robots=document.querySelector('meta[name="robots"]') as HTMLMetaElement|null
    if(!robots){robots=document.createElement('meta');robots.name='robots';document.head.appendChild(robots)}
    robots.content=privatePage?'noindex,nofollow':'index,follow'
  },[location.pathname])
  return null
}

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
function ClientRoute({children}:{children:React.ReactNode}){const session=getSession();const location=useLocation();if(!session){const returnTo=encodeURIComponent(`${location.pathname}${location.search}${location.hash}`);return <Navigate to={`/login?returnTo=${returnTo}`} replace/>}if(session.is_admin)return <Navigate to="/admin/dashboard" replace/>;return <>{children}</>}
function AdminRoute({children}:{children:React.ReactNode}){const session=getSession();const location=useLocation();if(!session){const returnTo=encodeURIComponent(`${location.pathname}${location.search}${location.hash}`);return <Navigate to={`/admin/login?returnTo=${returnTo}`} replace/>}if(!session.is_admin)return <Navigate to="/my-orders" replace/>;return <>{children}</>}

export default function App(){return <div className="app-shell"><RouteMetadata/><NavBar/><main className="container page-content"><Routes>
 <Route path="/" element={<Home/>}/><Route path="/service/:id" element={<ServiceDetail/>}/><Route path="/jobs" element={<Category/>}/><Route path="/scholarships" element={<Category/>}/><Route path="/meeseva" element={<Category/>}/><Route path="/certificates" element={<Category/>}/><Route path="/schemes" element={<Category/>}/><Route path="/about" element={<About/>}/><Route path="/contact" element={<Contact/>}/><Route path="/privacy" element={<PrivacyPolicy/>}/><Route path="/terms" element={<Terms/>}/><Route path="/disclaimer" element={<Disclaimer/>}/>
 <Route path="/login" element={<AuthRedirect><Login/></AuthRedirect>}/><Route path="/register" element={<AuthRedirect><Register/></AuthRedirect>}/><Route path="/admin/login" element={<AuthRedirect><AdminLogin/></AuthRedirect>}/><Route path="/request-reset" element={<RequestReset/>}/><Route path="/reset-password" element={<ResetPassword/>}/>
 <Route path="/my-orders" element={<ClientRoute><MyOrders/></ClientRoute>}/><Route path="/my-orders/:id" element={<ClientRoute><OrderDetail/></ClientRoute>}/><Route path="/account-settings" element={<ClientRoute><AccountSettings/></ClientRoute>}/><Route path="/grievances" element={<ClientRoute><MyGrievances/></ClientRoute>}/><Route path="/submit-grievance" element={<ClientRoute><SubmitGrievance/></ClientRoute>}/><Route path="/submit-review" element={<ClientRoute><SubmitReview/></ClientRoute>}/><Route path="/admin/*" element={<AdminRoute><AdminPanel/></AdminRoute>}/><Route path="*" element={<NotFound/>}/>
 </Routes></main><Footer/></div>}
