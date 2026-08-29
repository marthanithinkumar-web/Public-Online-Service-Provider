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
import SupportMessages from './pages/SupportMessages'
import SupportChatLauncher from './components/ui/SupportChatLauncher'
import Seo,{SITE} from './components/ui/Seo'

const PUBLIC_METADATA:Record<string,{title:string;description:string}>={
  '/':{title:'Public Online Service Provider — Application Assistance',description:'Find independent assistance for PAN cards, certificates, government jobs, scholarships, schemes, MeeSeva and other public-service applications.'},
  '/jobs':{title:'Government Job Application Assistance',description:'Explore independent help with government job searches, recruitment applications, corrections and application-status processes.'},
  '/scholarships':{title:'Scholarship Application Assistance',description:'Explore independent application help for eligible scholarships, renewals and scholarship status checks.'},
  '/meeseva':{title:'MeeSeva and Online Public Service Assistance',description:'Find independent assistance for eligible MeeSeva and other online public-service applications.'},
  '/certificates':{title:'Government Certificate Application Assistance',description:'Explore help with eligible income, caste, residence, birth, death and other certificate applications.'},
  '/schemes':{title:'Government Scheme Application Assistance',description:'Explore independent eligibility and application assistance for government schemes and welfare services.'},
  '/about':{title:'About Public Online Service Provider',description:'Learn how Public Online Service Provider offers private, independent assistance for public-service applications.'},
  '/contact':{title:'Contact Public Online Service Provider',description:'Contact Public Online Service Provider for help choosing an available public-service assistance option.'},
  '/privacy':{title:'Privacy Policy',description:'Read how Public Online Service Provider handles account, request and service information.'},
  '/terms':{title:'Terms and Conditions',description:'Read the terms that apply when using Public Online Service Provider.'},
  '/disclaimer':{title:'Independent Provider Disclaimer',description:'Public Online Service Provider is an independent private assistance platform, not a government department or official portal.'},
}
function RouteMetadata(){
  const location=useLocation()
  const path=location.pathname.replace(/\/$/,'')||'/'
  if(path.startsWith('/services/')||path.startsWith('/service/'))return null
  const metadata=PUBLIC_METADATA[path]
  const index=Boolean(metadata)
  const schema=path==='/'?[
    {'@context':'https://schema.org','@type':'WebSite',name:SITE.name,url:SITE.url,description:SITE.description,inLanguage:'en-IN'},
    {'@context':'https://schema.org','@type':'Organization',name:SITE.name,url:SITE.url,email:'marthanithinkumar@gmail.com',telephone:['+91-9063403352','+91-6281054602'],description:'Independent private assistance provider for public-service applications.'},
  ]:metadata?{'@context':'https://schema.org','@type':'WebPage',name:metadata.title,url:`${SITE.url}${path}`,description:metadata.description,isPartOf:{'@type':'WebSite',name:SITE.name,url:SITE.url}}:undefined
  return <Seo title={metadata?.title||'Private account page'} description={metadata?.description||'Private account or authentication page for Public Online Service Provider.'} path={path} index={index} schema={schema}/>
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

export default function App(){return <div className="app-shell"><RouteMetadata/><a className="skip-link" href="#main-content">Skip to main content</a><NavBar/><main id="main-content" tabIndex={-1} className="container page-content"><Routes>
 <Route path="/" element={<Home/>}/><Route path="/services/:slug" element={<ServiceDetail/>}/><Route path="/service/:id" element={<ServiceDetail/>}/><Route path="/jobs" element={<Category/>}/><Route path="/scholarships" element={<Category/>}/><Route path="/meeseva" element={<Category/>}/><Route path="/certificates" element={<Category/>}/><Route path="/schemes" element={<Category/>}/><Route path="/about" element={<About/>}/><Route path="/contact" element={<Contact/>}/><Route path="/privacy" element={<PrivacyPolicy/>}/><Route path="/terms" element={<Terms/>}/><Route path="/disclaimer" element={<Disclaimer/>}/>
 <Route path="/login" element={<AuthRedirect><Login/></AuthRedirect>}/><Route path="/register" element={<AuthRedirect><Register/></AuthRedirect>}/><Route path="/admin/login" element={<AuthRedirect><AdminLogin/></AuthRedirect>}/><Route path="/request-reset" element={<RequestReset/>}/><Route path="/admin/request-reset" element={<RequestReset accountType="admin"/>}/><Route path="/reset-password" element={<ResetPassword/>}/>
 <Route path="/my-orders" element={<ClientRoute><MyOrders/></ClientRoute>}/><Route path="/my-orders/:id" element={<ClientRoute><OrderDetail/></ClientRoute>}/><Route path="/account-settings" element={<ClientRoute><AccountSettings/></ClientRoute>}/><Route path="/messages" element={<ClientRoute><SupportMessages/></ClientRoute>}/><Route path="/grievances" element={<ClientRoute><MyGrievances/></ClientRoute>}/><Route path="/submit-grievance" element={<ClientRoute><SubmitGrievance/></ClientRoute>}/><Route path="/submit-review" element={<ClientRoute><SubmitReview/></ClientRoute>}/><Route path="/admin/*" element={<AdminRoute><AdminPanel/></AdminRoute>}/><Route path="*" element={<NotFound/>}/>
 </Routes></main><SupportChatLauncher/><Footer/></div>}
