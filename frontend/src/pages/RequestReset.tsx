import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'
import AuthLayout from '../components/ui/AuthLayout'
import {Link} from 'react-router-dom'

export default function RequestReset({accountType='client'}:{accountType?:'client'|'admin'}){
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error,setError]=useState('');const [busy,setBusy]=useState(false)

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault();if(busy)return;setMessage('');setError('');setBusy(true)
    try{
      const res = await axios.post(`${apiBase}/auth/request-password-reset`, { email, account_type:accountType })
      setMessage(res.data.message);setEmail('')
    }catch(err:any){
      setError(err?.response?.data?.error || 'Unable to request a reset link. Please try again.')
    }finally{setBusy(false)}
  }

  return (
    <AuthLayout title={accountType==='admin'?'Admin Password Recovery':'Password Recovery'} eyebrow="Secure account access"><div className="auth-card auth-card-modern"><div className="auth-intro"><h2>Reset your {accountType==='admin'?'administrator ':''}password</h2><p>Enter your {accountType==='admin'?'administrator':'client'} account email. If it exists, we’ll send a one-time reset link that expires in one hour.</p></div><form onSubmit={submit} className="auth-form"><label className="form-label">Email address<input className="form-input" type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>{error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button className="btn btn-primary btn-block" type="submit" disabled={busy}>{busy?'Sending…':'Send reset link'}</button></form><div className="auth-footer"><Link to={accountType==='admin'?'/admin/login':'/login'}>← Back to {accountType==='admin'?'admin ':''}login</Link></div></div></AuthLayout>
  )
}
