import React, { useState } from 'react'
import axios from 'axios'

export default function SubmitGrievance(){
  const [form, setForm] = useState({ order_id:'', client_name:'', phone:'', email:'', description:'' })
  const [msg, setMsg] = useState('')

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const payload:any = { client_name: form.client_name, phone: form.phone, description: form.description }
      if(form.order_id) payload.order_id = Number(form.order_id)
      if(form.email) payload.email = form.email
      const res = await axios.post('/api/grievances', payload)
      setMsg(res.data.message + (res.data.grievance ? (' Code: '+res.data.grievance.grievance_code) : ''))
      setForm({ order_id:'', client_name:'', phone:'', email:'', description:'' })
    }catch(err:any){
      setMsg(err?.response?.data?.error || 'Error')
    }
  }

  return (
    <div>
      <h1>Submit Grievance</h1>
      <form onSubmit={submit} className="request-form">
        <label>Related Order ID (optional)</label>
        <input value={form.order_id} onChange={e=>setForm({...form, order_id:e.target.value})} />
        <label>Full name</label>
        <input value={form.client_name} required onChange={e=>setForm({...form, client_name:e.target.value})} />
        <label>Phone</label>
        <input value={form.phone} required onChange={e=>setForm({...form, phone:e.target.value})} />
        <label>Email (optional)</label>
        <input value={form.email} onChange={e=>setForm({...form, email:e.target.value})} />
        <label>Description</label>
        <textarea value={form.description} onChange={e=>setForm({...form, description:e.target.value})} />
        <button type="submit">Submit Grievance</button>
      </form>
      {msg && <p className="info">{msg}</p>}
    </div>
  )
}
