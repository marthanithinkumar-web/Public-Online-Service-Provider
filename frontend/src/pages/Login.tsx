import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { login } from '../services/auth'

export default function Login(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const nav = useNavigate()

  const submit = async (e: React.FormEvent)=>{
    e.preventDefault(); setError(''); setBusy(true)
    try{
      const res = await login(email, password)
      if(res?.token) nav('/my-orders')
      else setError(res?.error || 'Login failed. Please check your details.')
    }catch(err:any){ setError(err?.response?.data?.error || 'Unable to sign in right now.') }
    finally{ setBusy(false) }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-intro">
          <span className="eyebrow">Welcome back</span>
          <h1>Sign in to your service account</h1>
          <p>Track requests, manage your profile and stay updated on your public service applications.</p>
        </div>
        <form onSubmit={submit} className="auth-form" aria-label="Client login form">
          <label>Email address<input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>
          <label>Password<input type="password" autoComplete="current-password" required value={password} onChange={e=>setPassword(e.target.value)} /></label>
          {error && <p className="info" role="alert">{error}</p>}
          <button type="submit" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
          <Link className="auth-secondary-link" to="/request-reset">Forgot your password?</Link>
        </form>
        <div className="auth-footer">New here? <Link to="/register">Create your account</Link></div>
      </div>
    </div>
  )
}
