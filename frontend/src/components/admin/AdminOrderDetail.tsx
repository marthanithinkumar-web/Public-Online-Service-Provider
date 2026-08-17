import React, { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import axios from 'axios'
import { authHeader } from '../../services/auth'

export default function AdminOrderDetail(){
  const { id } = useParams()
  const [data, setData] = useState<any|null>(null)

  useEffect(()=>{
    if(!id) return
    const load = async ()=>{
      try{
        const res = await axios.get(`/api/admin/orders/${id}`, { headers: authHeader() })
        setData(res.data)
      }catch(err){ console.error(err) }
    }
    load()
  }, [id])

  if(!data) return <p>Loading...</p>

  return (
    <div>
      <h2>Order {data.order.order_code}</h2>
      <div><strong>Client:</strong> {data.order.client_name} • {data.order.phone}</div>
      <div><strong>Service:</strong> {data.order.service}</div>
      <div><strong>Status:</strong> {data.order.status}</div>
      <h3>History</h3>
      <ul>
        {data.history.map((h:any)=> (
          <li key={h.id}>{h.created_at}: {h.previous_status} → {h.new_status} by {h.changed_by} {h.note ? ' - '+h.note : ''}</li>
        ))}
      </ul>
      <h3>Attachments</h3>
      <ul>
        {data.attachments.map((a:any)=> (
          <li key={a.id}>{a.filename} <button onClick={async ()=>{
            try{
              const res = await fetch(`/api/uploads/${a.id}/download`, { headers: { Authorization: `Bearer ${localStorage.getItem('psp_token') || ''}` } })
              if(!res.ok) return alert('Download failed')
              const blob = await res.blob()
              const url = window.URL.createObjectURL(blob)
              const link = document.createElement('a')
              link.href = url
              link.download = a.filename
              document.body.appendChild(link)
              link.click()
              link.remove()
            }catch(err){ console.error(err); alert('Error') }
          }}>Download</button></li>
        ))}
      </ul>
      <h3>Grievances</h3>
      <ul>
        {data.grievances.map((g:any)=> (
          <li key={g.id}>{g.grievance_code} - {g.status} - {g.description}</li>
        ))}
      </ul>
      <h3>Reviews</h3>
      <ul>
        {data.reviews.map((r:any)=> (
          <li key={r.id}>Rating: {r.rating} — {r.comment}</li>
        ))}
      </ul>
    </div>
  )
}
