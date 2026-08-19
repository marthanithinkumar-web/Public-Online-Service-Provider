import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../services/auth'

export default function Register(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault(); setError('')
    if(password !== confirm){ setError('Passwords do not match.'); return }
    setBusy(true)
    try{
      const res = await register(email, password)
      if(res?.token) nav('/my-orders')
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
          <label>Email address<input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label>Password<input type="password" autoComplete="new-password" minLength={8} required value={password} onChange={e=>setPassword(e.target.value)} /></label>
          <label>Confirm password<input type="password" autoComplete="new-password" minLength={8} required value={confirm} onChange={e=>setConfirm(e.target.value)} /></label>
          <p className="auth-hint">Use at least 8 characters for your password.</p>
          {error && <p className="info" role="alert">{error}</p>}
          <button type="submit" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
        </form>
        <div className="auth-footer">Already have an account? <Link to="/login">Sign in</Link></div>
      </div>
    </div>
  )
}
