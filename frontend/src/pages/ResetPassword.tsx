import React, { useState } from 'react'
import axios from 'axios'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { apiBase } from '../services/apiBase'

export default function ResetPassword(){
  const [params]=useSearchParams()
  const token=params.get('token')||''
  const [newPassword, setNewPassword] = useState('')
  const [confirm,setConfirm]=useState('')
  const [message, setMessage] = useState('')
  const [error,setError]=useState('');const [busy,setBusy]=useState(false)
  const nav = useNavigate()

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault();if(busy)return;setMessage('');setError('')
    if(!token){setError('This reset link is incomplete. Request a new password reset link.');return}
    if(newPassword.length<8){setError('Use at least 8 characters for your new password.');return}
    if(newPassword!==confirm){setError('The passwords do not match.');return}
    setBusy(true)
    try{
      const res = await axios.post(`${apiBase}/auth/reset-password`, { token, new_password: newPassword })
      setMessage(res.data.message)
      if(res.data.message?.toLowerCase().includes('successful')){
        setTimeout(()=>nav('/login'), 1200)
      }
    }catch(err:any){
      setError(err?.response?.data?.error || 'Unable to reset your password. Request a new link and try again.')
    }finally{setBusy(false)}
  }

  return (
    <div className="auth-page"><div className="auth-card"><div className="auth-intro"><span className="eyebrow">Account recovery</span><h1>Choose a new password</h1><p>Your new password must contain at least eight characters.</p></div>{!token?<div className="dashboard-state error-state"><p>This reset link is incomplete or invalid.</p><Link className="btn btn-primary" to="/request-reset">Request a new link</Link></div>:<form onSubmit={submit} className="auth-form"><label>New password<input type="password" minLength={8} autoComplete="new-password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} required /></label><label>Confirm new password<input type="password" minLength={8} autoComplete="new-password" value={confirm} onChange={e=>setConfirm(e.target.value)} required /></label>{error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button type="submit" disabled={busy}>{busy?'Updating…':'Set new password'}</button></form>}</div></div>
  )
}
