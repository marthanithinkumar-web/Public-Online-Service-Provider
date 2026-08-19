import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { apiBase } from '../services/apiBase'
import { deleteAccount } from '../services/auth'

export default function AccountSettings(){
  const navigate = useNavigate()
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const handleDelete = async (event: React.FormEvent) => {
    event.preventDefault(); setMessage(''); setError('')
    if(!password){ setError('Enter your current password to continue.'); return }
    if(password !== confirm){ setError('The passwords do not match.'); return }
    if(!window.confirm('This permanently deletes your account and client-owned data. This action cannot be undone. Continue?')) return
    try{
      setBusy(true)
      await deleteAccount(password)
      setMessage('Your account has been permanently deleted. Redirecting to the home page…')
      setPassword(''); setConfirm('')
      window.setTimeout(() => navigate('/'), 1200)
    }catch(err){
      setError(axios.isAxiosError(err) ? (err.response?.data?.error || 'Unable to delete the account.') : 'Unable to delete the account. Please try again.')
    }finally{ setBusy(false) }
  }

  return (
    <div className="settings-page">
      <section className="dashboard-hero settings-hero">
        <div><span className="eyebrow">Your account</span><h1>Account settings</h1><p>Manage your account, privacy choices and security-sensitive actions.</p></div>
        <Link className="btn btn-secondary" to="/my-orders">Back to requests</Link>
      </section>

      <div className="settings-grid">
        <section className="dashboard-section settings-card">
          <span className="eyebrow">Account</span><h2>Service account</h2>
          <p>Your account gives you a single place to track public-service requests, submit grievances and leave reviews.</p>
          <div className="settings-links"><Link to="/my-orders">My requests <span>→</span></Link><Link to="/submit-grievance">Get help with a request <span>→</span></Link><Link to="/submit-review">Share a service review <span>→</span></Link></div>
        </section>

        <section className="dashboard-section settings-card danger-card">
          <span className="eyebrow">Privacy & security</span><h2>Delete account</h2>
          <p>Permanently removes your client account and associated client-owned orders, grievances, reviews and uploaded files.</p>
          <p className="auth-hint">Your current password is required. This cannot be undone.</p>
          <form onSubmit={handleDelete} className="auth-form settings-delete-form">
            <label>Current password<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} disabled={busy}/></label>
            <label>Confirm current password<input type="password" autoComplete="current-password" value={confirm} onChange={e=>setConfirm(e.target.value)} disabled={busy}/></label>
            {error && <p className="info" role="alert">{error}</p>}
            {message && <p className="success-message" role="status">{message}</p>}
            <button className="danger-button" type="submit" disabled={busy}>{busy ? 'Deleting account…' : 'Permanently delete my account'}</button>
          </form>
        </section>
      </div>

      <p className="settings-api-link"><a href={`${apiBase.replace(/\/api$/, '')}/`}>Service provider API</a></p>
    </div>
  )
}
