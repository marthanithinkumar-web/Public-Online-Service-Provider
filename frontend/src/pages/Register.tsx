import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { register } from '../services/auth'
import '../styles/auth.css'

export default function Register(){
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()
  const location=useLocation();const requestedReturn=new URLSearchParams(location.search).get('returnTo')
  const safeReturn=requestedReturn&&requestedReturn.startsWith('/')&&!requestedReturn.startsWith('//')?requestedReturn:'/my-orders'

  const validatePhone = (p:string) => {
    // basic 10-digit validation (allow digits, spaces, + and -)
    const cleaned = p.replace(/[^0-9]/g, '')
    return cleaned.length >= 10 && cleaned.length <= 15
  }

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault(); setError('')
    if(!name.trim()){ setError('Name is required.'); return }
    if(!phone.trim() || !validatePhone(phone)){ setError('Valid phone number is required.'); return }
    if(!email.trim()){ setError('Email is required.'); return }
    if(!password){ setError('Password is required.'); return }
    if(password !== confirm){ setError('Passwords do not match.'); return }
    setBusy(true)
    try{
      const res = await register(name.trim(), phone.trim(), email.trim(), password)
      if(res?.token) nav(safeReturn,{replace:true})
      else setError(res?.error || 'Registration failed. Please check your details.')
    }catch(err:any){ setError(err?.response?.data?.error || 'Unable to create your account right now.') }
    finally{ setBusy(false) }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-intro">
          <span className="eyebrow">Get started</span>
          <h1>Create your service account</h1>
          <p>Keep your requests organized and access your service history from one secure place.</p>
        </div>
        <form onSubmit={submit} className="auth-form" aria-label="Client registration form">
          <label>Name<span className="required">*</span><input type="text" autoComplete="name" required value={name} onChange={e=>setName(e.target.value)} /></label>
          <label>Phone number<span className="required">*</span><input type="tel" autoComplete="tel" required value={phone} onChange={e=>setPhone(e.target.value)} /></label>
          <label>Email address<span className="required">*</span><input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label>Password<span className="required">*</span><input type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e=>setPassword(e.target.value)} /></label>
          <label>Confirm password<span className="required">*</span><input type="password" autoComplete="new-password" minLength={8} required value={confirm} onChange={e=>setConfirm(e.target.value)} /></label>
          <p className="auth-hint">Use at least 8 characters for your password.</p>
          {error && <p className="info" role="alert">{error}</p>}
          <button type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
        </form>
        <div className="auth-footer">Already have an account? <Link to={`/login${requestedReturn?`?returnTo=${encodeURIComponent(safeReturn)}`:''}`}>Sign in</Link></div>
      </div>
    </div>
  )
}
