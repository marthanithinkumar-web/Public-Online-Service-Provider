import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { register } from '../services/auth'

export default function Register(){
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const nav = useNavigate()

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const res = await register(email, password)
      if(res?.token){
        nav('/my-orders')
      }else{
        setError(res?.error || 'Registration failed')
      }
    }catch(err:any){
      setError(err?.response?.data?.error || 'Error')
    }
  }

  return (
    <div>
      <h1>Register</h1>
      <form onSubmit={submit} className="auth-form">
        <label>Email</label>
        <input type="email" required value={email} onChange={e=>setEmail(e.target.value)} />
        <label>Password</label>
        <input type="password" required value={password} onChange={e=>setPassword(e.target.value)} />
        <button type="submit">Create account</button>
      </form>
      {error && <p className="info">{error}</p>}
    </div>
  )
}
