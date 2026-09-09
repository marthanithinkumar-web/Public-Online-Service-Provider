import React,{useState} from 'react'
import {Link,useLocation,useNavigate} from 'react-router-dom'
import {login} from '../../services/auth'
import AuthLayout from '../ui/AuthLayout'

export default function AdminLogin(){
  const [email,setEmail]=useState('')
  const [password,setPassword]=useState('')
  const [showPassword,setShowPassword]=useState(false)
  const [error,setError]=useState('')
  const [busy,setBusy]=useState(false)
  const nav=useNavigate()
  const location=useLocation()
  const requestedReturn=new URLSearchParams(location.search).get('returnTo')
  const safeReturn=requestedReturn&&requestedReturn.startsWith('/admin/')&&!requestedReturn.startsWith('//')?requestedReturn:'/admin/dashboard'

  const submit=async(e:React.FormEvent)=>{
    e.preventDefault()
    if(busy)return
    setError('')
    setBusy(true)
    try{
      const res=await login(email,password)
      if(res?.user?.is_admin)nav(safeReturn,{replace:true})
      else setError('This account does not have administrator access.')
    }catch(err:any){
      setError(err?.code==='ECONNABORTED'?'The secure server took too long to respond. Please try again.':err?.response?.data?.error||'Unable to sign in. Please check your details.')
    }finally{
      setBusy(false)
    }
  }

  return <AuthLayout title="Admin Login" eyebrow="Administration portal">
    <div className="auth-card auth-card-modern" role="region" aria-labelledby="admin-login-heading">
      <div className="auth-intro">
        <h2 id="admin-login-heading">Secure administrator access</h2>
        <p>Manage requests, services, grievances and client updates.</p>
      </div>
      <form onSubmit={submit} className="auth-form" aria-label="Administrator login form">
        <label className="form-label">Email address
          <input className="form-input" type="email" autoComplete="username" required value={email} onChange={event=>setEmail(event.target.value)}/>
        </label>
        <label className="form-label">Password
          <div className="password-field">
            <input className="form-input" type={showPassword?'text':'password'} autoComplete="current-password" required value={password} onChange={event=>setPassword(event.target.value)}/>
            <button type="button" aria-label={showPassword?'Hide password':'Show password'} className="password-toggle" onClick={()=>setShowPassword(value=>!value)}>{showPassword?'Hide':'Show'}</button>
          </div>
        </label>
        {error&&<p className="info" role="alert">{error}</p>}
        {busy&&<p className="auth-hint" role="status">Connecting securely… The server may take a few seconds on the first visit.</p>}
        <button className="btn btn-primary btn-block" type="submit" disabled={busy}>{busy?'Checking…':'Sign in securely'}</button>
      </form>
      <div className="auth-footer">
        <Link to="/admin/request-reset">Forgot administrator password?</Link>
        <Link to="/">← Back to public site</Link>
      </div>
    </div>
  </AuthLayout>
}
