import React, { useState } from 'react'
import axios from 'axios'

export default function Contact(){
  const [form, setForm] = useState({ name:'', email:'', phone:'', message:'' })
  const [msg, setMsg] = useState('')

  const submit = async (e:any)=>{
    e.preventDefault()
    // For now, just show message — in future this can POST to backend inbox
    setMsg('Thank you. We will contact you soon.')
    setForm({ name:'', email:'', phone:'', message:'' })
  }

  return (
    <div>
      <h1>Contact</h1>
      <p>Provider: <strong>Provider Name</strong> • Phone: 9999999999 • Email: provider@example.com</p>
      <form onSubmit={submit} className="request-form">
        <label>Name</label>
        <input value={form.name} onChange={e=>setForm({...form, name:e.target.value})} />
        <label>Email</label>
        <input value={form.email} onChange={e=>setForm({...form, email:e.target.value})} />
        <label>Phone</label>
        <input value={form.phone} onChange={e=>setForm({...form, phone:e.target.value})} />
        <label>Message</label>
        <textarea value={form.message} onChange={e=>setForm({...form, message:e.target.value})} />
        <button type="submit">Send</button>
      </form>
      {msg && <p className="info">{msg}</p>}
    </div>
  )
}
