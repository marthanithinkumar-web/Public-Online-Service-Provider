import React,{useState} from 'react'
import axios from 'axios'
import {Link} from 'react-router-dom'
import AuthLayout from '../components/ui/AuthLayout'
import {apiBase} from '../services/apiBase'

export default function RequestVerification(){
  const [email,setEmail]=useState('');const [message,setMessage]=useState('');const [busy,setBusy]=useState(false)
  const submit=async(event:React.FormEvent)=>{event.preventDefault();setBusy(true);setMessage('');try{const response=await axios.post(`${apiBase}/auth/request-verify`,{email},{timeout:15000});setMessage(response.data.message)}catch{setMessage('Unable to request a verification link right now.')}finally{setBusy(false)}}
  return <AuthLayout title="Email Verification" eyebrow="Secure account activation"><div className="auth-card auth-card-modern"><div className="auth-intro"><h2>Request a new verification link</h2><p>Enter the email address used for your client account.</p></div><form className="auth-form" onSubmit={submit}><label className="form-label">Email address<input className="form-input" type="email" autoComplete="email" required value={email} onChange={event=>setEmail(event.target.value)}/></label>{message&&<p className="success-message" role="status">{message}</p>}<button className="btn btn-primary btn-block" disabled={busy}>{busy?'Sending…':'Send verification link'}</button></form><div className="auth-footer"><Link to="/login">← Back to client login</Link></div></div></AuthLayout>
}
