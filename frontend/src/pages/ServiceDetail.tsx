import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'

export default function ServiceDetail(){
  const { id } = useParams()
  const [service, setService] = useState<any|null>(null)
  const [form, setForm] = useState({ client_name: '', phone: '', email: '', description: '' })
  const [message, setMessage] = useState('')
  const [lastOrder, setLastOrder] = useState<any|null>(null)
  const [file, setFile] = useState<File | null>(null)
  const [uploadMsg, setUploadMsg] = useState('')

  useEffect(()=>{
    if(!id) return
    axios.get(`/api/services/${id}`).then(r=>setService(r.data)).catch(()=>{})
  }, [id])

  const submit = async (e:any)=>{
    e.preventDefault()
    try{
      const payload = { ...form, service_id: Number(id) }
      const res = await axios.post('/api/orders', payload)
      setMessage(res.data.message + ' Order: ' + res.data.order.order_code)
      setLastOrder(res.data.order)
      setForm({ client_name: '', phone: '', email: '', description: '' })
    }catch(err:any){
      setMessage(err?.response?.data?.error || 'Error submitting')
    }
  }

  const uploadFile = async (e:any)=>{
    e.preventDefault()
    if(!file || !lastOrder) return setUploadMsg('Select file and ensure order exists')
    const fd = new FormData()
    fd.append('file', file)
    fd.append('order_id', String(lastOrder.id))
    try{
      const res = await axios.post('/api/uploads', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setUploadMsg(res.data.message)
    }catch(err:any){
      setUploadMsg(err?.response?.data?.error || 'Upload failed')
    }
  }

  return (
    <div>
      {service ? (
        <div>
          <h1>{service.name}</h1>
          <p><strong>Category:</strong> {service.category}</p>
          <p>{service.description}</p>
          <p><strong>Fee:</strong> ₹{service.price_inr}</p>

          <section>
            <h2>Request Assistance</h2>
            <div style={{background:'#eef9fb',padding:12,borderRadius:6,marginBottom:12}}>
              <strong>Provider:</strong> {service.provider_name || 'Provider Name'} • <a href={`tel:${service.provider_phone || '9999999999'}`}>{service.provider_phone || '9999999999'}</a> • <a href={`mailto:${service.provider_email || 'provider@example.com'}`}>{service.provider_email || 'provider@example.com'}</a>
              <div style={{marginTop:8,fontSize:12,color:'#666'}}>Privacy: We will never ask for OTPs, passwords, PINs, or bank details.</div>
            </div>
            <form onSubmit={submit} className="request-form">
              <label>Full name</label>
              <input value={form.client_name} onChange={e=>setForm({...form, client_name: e.target.value})} required />
              <label>Phone</label>
              <input value={form.phone} onChange={e=>setForm({...form, phone: e.target.value})} required />
              <label>Email (optional)</label>
              <input value={form.email} onChange={e=>setForm({...form, email: e.target.value})} />
              <label>Short description / Notes</label>
              <textarea value={form.description} onChange={e=>setForm({...form, description: e.target.value})} />
              <button type="submit">Submit Request</button>
            </form>
            {message && <p className="info">{message}</p>}

            {lastOrder && (
              <div style={{marginTop:16}}>
                <h3>Attach a document (optional)</h3>
                <form onSubmit={uploadFile} encType="multipart/form-data">
                  <input type="file" onChange={e=>setFile(e.target.files?.[0] ?? null)} accept=".pdf,.png,.jpg,.jpeg" />
                  <button type="submit">Upload</button>
                </form>
                {uploadMsg && <p className="info">{uploadMsg}</p>}
              </div>
            )}

          </section>

        </div>
      ) : (
        <p>Loading...</p>
      )}
    </div>
  )
}
