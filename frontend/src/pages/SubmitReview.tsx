import React, { useState } from 'react'
import axios from 'axios'
import { apiBase } from '../services/apiBase'

export default function SubmitReview(){
  const [form, setForm] = useState({ order_id:'', rating:5, comment:'', client_name:'' })
  const [msg, setMsg] = useState('')

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const payload:any = { rating: Number(form.rating), comment: form.comment }
      if(form.order_id) payload.order_id = Number(form.order_id)
      if(form.client_name) payload.client_name = form.client_name
      const res = await axios.post(`${apiBase}/reviews`, payload)
      setMsg(res.data.message)
      setForm({ order_id:'', rating:5, comment:'', client_name:'' })
    }catch(err:any){
      setMsg(err?.response?.data?.error || 'Error')
    }
  }

  return (
    <div>
      <h1>Submit Review</h1>
      <form onSubmit={submit} className="request-form">
        <label>Related Order ID (optional)</label>
        <input value={form.order_id} onChange={e=>setForm({...form, order_id:e.target.value})} />
        <label>Rating (1-5)</label>
        <input type="number" min={1} max={5} value={form.rating} onChange={e=>setForm({...form, rating:Number(e.target.value)})} />
        <label>Comment</label>
        <textarea value={form.comment} onChange={e=>setForm({...form, comment:e.target.value})} />
        <label>Your name (optional)</label>
        <input value={form.client_name} onChange={e=>setForm({...form, client_name:e.target.value})} />
        <button type="submit">Submit Review</button>
      </form>
      {msg && <p className="info">{msg}</p>}
    </div>
  )
}
