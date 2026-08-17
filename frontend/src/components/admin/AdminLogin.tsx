import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../../services/auth'

export default function AdminLogin(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const nav = useNavigate()

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const res = await login(email, password)
      if(res?.user?.is_admin){
        nav('/admin/dashboard')
      }else{
        setError('Not an admin account')
      }
    }catch(err:any){
      setError(err?.response?.data?.error || 'Login failed')
    }
  }

  return (
    <div style={{maxWidth:420,margin:'40px auto'}}>
      <h2>Admin Login</h2>
      <form onSubmit={submit} className="auth-form">
        <label>Email</label>
        <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} />
        <label>Password</label>
        <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit">Sign in</button>
      </form>
      {error && <p className="info">{error}</p>}
    </div>
  )
}
