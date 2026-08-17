import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'

export default function RequestReset(){
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const res = await axios.post(`${apiBase}/auth/request-password-reset`, { email })
      setMessage(res.data.message + (res.data.reset_token ? (' Token: '+res.data.reset_token) : ''))
    }catch(err:any){
      setMessage(err?.response?.data?.error || 'Error')
    }
  }

  return (
    <div>
      <h1>Request Password Reset</h1>
      <form onSubmit={submit} className="auth-form">
        <label>Email</label>
        <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} />
        <button type="submit">Send Reset Link</button>
      </form>
      {message && <p className="info">{message}</p>}
    </div>
  )
}
