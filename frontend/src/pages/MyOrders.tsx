import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { authHeader } from '../services/auth'

export default function MyOrders(){
  const [orders, setOrders] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{
    const fetch = async ()=>{
      try{
        const res = await axios.get('/api/orders/mine', { headers: authHeader() })
        setOrders(res.data)
      }catch(err){
        console.error(err)
      }finally{
        setLoading(false)
      }
    }
    fetch()
  }, [])

  if(loading) return <p>Loading...</p>

  return (
    <div>
      <h1>My Orders</h1>
      {orders.length===0 && <p>No orders found.</p>}
      <ul>
        {orders.map(o=> (
          <li key={o.id} className="service-card">
            <h3>{o.order_code} - {o.service}</h3>
            <p>Status: {o.status}</p>
            <p>Fee: ₹{o.fee_inr}</p>
            <p>Submitted: {new Date(o.created_at).toLocaleString()}</p>
            <div style={{marginTop:8}}>
              <a href={`/submit-grievance`} style={{marginRight:8}}>Submit Grievance</a>
              <a href={`/submit-review`}>Submit Review</a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
