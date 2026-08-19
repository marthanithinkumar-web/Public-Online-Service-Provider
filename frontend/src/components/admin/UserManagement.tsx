import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authHeader, logout } from '../../services/auth'
import { apiBase } from '../../services/apiBase'

export default function UserManagement(){
  const [items,setItems] = useState<any[]>([])
  const [err,setErr] = useState('')
  const [loading,setLoading] = useState(true)
  const nav = useNavigate()

  useEffect(()=>{
    let cancelled = false

    ;(async ()=>{
      try{
        setLoading(true)
        setErr('')
        const res = await fetch(`${apiBase}/admin/users`, {
          headers: Object.assign({ 'Content-Type':'application/json' }, authHeader() as Record<string,string>)
        })

        if (res.status === 401 || res.status === 403) {
          if (!cancelled) {
            logout()
            nav('/admin/login', { replace: true })
          }
          return
        }

        if(!res.ok){
          if (!cancelled) setErr(`Unable to load users (HTTP ${res.status})`)
          return
        }

        const data = await res.json()
        if (!cancelled) setItems(Array.isArray(data.items) ? data.items : [])
      }catch(e:any){
        if (!cancelled) setErr('Unable to load users. Please sign in again and refresh.')
      }finally{
        if (!cancelled) setLoading(false)
      }
    })()

    return () => { cancelled = true }
  },[nav])

  return (
    <div>
      <h2>Registered clients</h2>
      {loading && <p className="info">Loading registered clients…</p>}
      {err && <p className="info" role="alert">{err}</p>}
      <table className="table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Joined</th></tr></thead>
        <tbody>
          {!loading && !err && items.length === 0 && (
            <tr><td colSpan={4}>No registered clients yet.</td></tr>
          )}
          {items.map(u=> (
            <tr key={u.id}>
              <td>{u.name || '—'}</td>
              <td>{u.email || '—'}</td>
              <td>{u.phone || '—'}</td>
              <td>{u.created_at ? new Date(u.created_at).toLocaleString() : '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
