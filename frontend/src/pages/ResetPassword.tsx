import React, { useState } from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

export default function ResetPassword(){
  const [token, setToken] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [message, setMessage] = useState('')
  const nav = useNavigate()

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const res = await axios.post('/api/auth/reset-password', { token, new_password: newPassword })
      setMessage(res.data.message)
      if(res.data.message?.toLowerCase().includes('successful')){
        setTimeout(()=>nav('/login'), 1200)
      }
    }catch(err:any){
      setMessage(err?.response?.data?.error || 'Error')
    }
  }

  return (
    <div>
      <h1>Reset Password</h1>
      <form onSubmit={submit} className="auth-form">
        <label>Token</label>
        <input value={token} onChange={e=>setToken(e.target.value)} required />
        <label>New password</label>
        <input type="password" value={newPassword} onChange={e=>setNewPassword(e.target.value)} required />
        <button type="submit">Set new password</button>
      </form>
      {message && <p className="info">{message}</p>}
    </div>
  )
}
