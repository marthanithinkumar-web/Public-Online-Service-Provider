import React, { useEffect, useState } from 'react'
import { authHeader } from '../../services/auth'
import { apiBase } from '../../services/apiBase'

export default function UserManagement(){
  const [items,setItems] = useState<any[]>([])
  const [err,setErr] = useState('')
  useEffect(()=>{
    (async ()=>{
      try{
        const res = await fetch(`${apiBase}/admin/users`, { headers: { ...authHeader(), 'Content-Type':'application/json' } })
        if(!res.ok){ setErr('Unable to load users'); return }
        const data = await res.json()
        setItems(Array.isArray(data.items) ? data.items : [])
      }catch(e:any){ setErr('Unable to load users') }
    })()
  },[])

  return (
    <div>
      <h2>Registered clients</h2>
      {err && <p className="info">{err}</p>}
      <table className="table">
        <thead><tr><th>Name</th><th>Email</th><th>Phone</th><th>Joined</th></tr></thead>
        <tbody>
          {items.map(u=> (
            <tr key={u.id}><td>{u.name}</td><td>{u.email}</td><td>{u.phone}</td><td>{new Date(u.created_at).toLocaleString()}</td></tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
