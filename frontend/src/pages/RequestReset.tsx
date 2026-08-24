import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'

export default function RequestReset(){
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error,setError]=useState('');const [busy,setBusy]=useState(false)

  const submit = async (e:React.FormEvent)=>{
    e.preventDefault();if(busy)return;setMessage('');setError('');setBusy(true)
    try{
      const res = await axios.post(`${apiBase}/auth/request-password-reset`, { email })
      setMessage(res.data.message);setEmail('')
    }catch(err:any){
      setError(err?.response?.data?.error || 'Unable to request a reset link. Please try again.')
    }finally{setBusy(false)}
  }

  return (
    <div className="auth-page"><div className="auth-card"><div className="auth-intro"><span className="eyebrow">Account recovery</span><h1>Reset your password</h1><p>Enter your account email. If it exists, we’ll send a secure reset link that expires in one hour.</p></div><form onSubmit={submit} className="auth-form"><label>Email address<input type="email" autoComplete="email" required value={email} onChange={e=>setEmail(e.target.value)} /></label>{error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button type="submit" disabled={busy}>{busy?'Sending…':'Send reset link'}</button></form></div></div>
  )
}
