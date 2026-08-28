import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { register } from '../services/auth'
import '../styles/auth.css'
import AuthLayout from '../components/ui/AuthLayout'
import {isValidEmail,normalizeEmail,normalizeIndianMobile} from '../services/contactValidation'

export default function Register(){
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [success,setSuccess]=useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()
  const location=useLocation();const requestedReturn=new URLSearchParams(location.search).get('returnTo')
  const safeReturn=requestedReturn&&requestedReturn.startsWith('/')&&!requestedReturn.startsWith('//')?requestedReturn:'/my-orders'

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault(); setError('');setSuccess('')
    if(name.trim().length<2||name.trim().length>200){ setError('Name must be between 2 and 200 characters.'); return }
    const normalizedPhone=normalizeIndianMobile(phone)
    const normalizedEmail=normalizeEmail(email)
    if(!normalizedPhone){ setError('Enter a valid Indian mobile number beginning with 6, 7, 8 or 9.'); return }
    if(!isValidEmail(normalizedEmail)){ setError('Enter a valid email address, for example name@example.com.'); return }
    if(!password){ setError('Password is required.'); return }
    if(password !== confirm){ setError('Passwords do not match.'); return }
    setBusy(true)
    try{
      const res = await register(name.trim(), normalizedPhone, normalizedEmail, password)
      if(res?.token) nav(safeReturn,{replace:true})
      else if(res?.verification_required){setSuccess(res.message);setPassword('');setConfirm('')}
      else setError(res?.error || 'Registration failed. Please check your details.')
    }catch(err:any){ setError(err?.code==='ECONNABORTED'?'The secure server took too long to respond. Please try again.':err?.response?.data?.error || 'Unable to create your account right now.') }
    finally{ setBusy(false) }
  }

  return (
    <AuthLayout title="Create Account" eyebrow="Public service account">
      <div className="auth-card auth-card-modern">
        <div className="auth-intro">
          <h2>Create your service account</h2>
          <p>Keep your requests organized and access your service history from one secure place.</p>
        </div>
        <form onSubmit={submit} className="auth-form" aria-label="Client registration form">
          <label className="form-label">Name<span className="required">*</span><input className="form-input" type="text" autoComplete="name" required value={name} onChange={e=>setName(e.target.value)} /></label>
          <label className="form-label">Phone number<span className="required">*</span><input className="form-input" type="tel" inputMode="tel" autoComplete="tel" maxLength={18} aria-describedby="phone-hint" placeholder="10-digit Indian mobile number" required value={phone} onChange={e=>setPhone(e.target.value)} /><small id="phone-hint" className="field-hint">Use a valid Indian mobile number beginning with 6, 7, 8 or 9. +91 is optional.</small></label>
          <label className="form-label">Email address<span className="required">*</span><input className="form-input" type="email" inputMode="email" autoComplete="email" maxLength={254} aria-describedby="email-hint" placeholder="name@example.com" required value={email} onChange={e=>setEmail(e.target.value)} /><small id="email-hint" className="field-hint">Enter a complete email address that you can access.</small></label>
          <label className="form-label">Password<span className="required">*</span><input className="form-input" type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e=>setPassword(e.target.value)} /></label>
          <label className="form-label">Confirm password<span className="required">*</span><input className="form-input" type="password" autoComplete="new-password" minLength={8} required value={confirm} onChange={e=>setConfirm(e.target.value)} /></label>
          <p className="auth-hint">Use at least 8 characters for your password.</p>
          {error && <p className="info" role="alert">{error}</p>}
          {success&&<p className="success-message" role="status">{success}</p>}
          <button className="btn btn-primary btn-block" type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
        </form>
        <div className="auth-footer">Already have an account? <Link to={`/login${requestedReturn?`?returnTo=${encodeURIComponent(safeReturn)}`:''}`}>Sign in</Link></div>
      </div>
    </AuthLayout>
  )
}
