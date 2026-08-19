import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
    event.preventDefault()
    setMessage('')
    setError('')

    if(password.length < 1){
      setError('Enter your current password to continue.')
      return
    }
    if(password !== confirm){
      setError('The passwords do not match.')
      return
    }

    const confirmed = window.confirm(
      'This permanently deletes your account and client-owned orders, grievances, reviews, and uploaded files. This action cannot be undone. Continue?'
    )
    if(!confirmed) return

    try{
      setBusy(true)
      await deleteAccount(password)
      setMessage('Your account has been permanently deleted. Redirecting to the home page...')
      setPassword('')
      setConfirm('')
      window.setTimeout(() => navigate('/'), 1200)
    }catch(err){
      if(axios.isAxiosError(err)){
        setError(err.response?.data?.error || 'Unable to delete the account.')
      }else{
        setError('Unable to delete the account. Please try again.')
      }
    }finally{
      setBusy(false)
    }
  }

  return (
    <div style={{maxWidth:720,margin:'40px auto'}}>
      <h1>Account Settings</h1>
      <p>Manage your client account and privacy choices.</p>

      <section className="service-card" style={{marginTop:24}}>
        <h2>Delete account</h2>
        <p>
          Deleting your account permanently removes your client account and associated client-owned
          orders, grievances, reviews, and uploaded files. This cannot be undone.
        </p>
        <p style={{fontSize:13,opacity:.8}}>
          For security, your current password is required.
        </p>

        <form onSubmit={handleDelete} style={{marginTop:18}}>
          <label style={{display:'block',marginBottom:12}}>
            Current password
            <input
              type="password"
              value={password}
              onChange={e=>setPassword(e.target.value)}
              autoComplete="current-password"
              disabled={busy}
              style={{display:'block',width:'100%',marginTop:6,padding:10}}
            />
          </label>

          <label style={{display:'block',marginBottom:16}}>
            Confirm current password
            <input
              type="password"
              value={confirm}
              onChange={e=>setConfirm(e.target.value)}
              autoComplete="current-password"
              disabled={busy}
              style={{display:'block',width:'100%',marginTop:6,padding:10}}
            />
          </label>

          {error && <p role="alert" style={{color:'#b42318'}}>{error}</p>}
          {message && <p role="status" style={{color:'#087443'}}>{message}</p>}

          <button
            type="submit"
            disabled={busy}
            style={{padding:'10px 16px',border:0,borderRadius:6,background:'#b42318',color:'#fff',cursor:busy?'wait':'pointer'}}
          >
            {busy ? 'Deleting account...' : 'Permanently Delete My Account'}
          </button>
        </form>
      </section>

      <p style={{marginTop:20}}>
        <a href={`${apiBase.replace(/\/api$/, '')}/`}>Service provider API</a>
      </p>
    </div>
  )
}
