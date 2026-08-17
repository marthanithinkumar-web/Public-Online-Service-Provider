import React, { useEffect, useState } from 'react'
import { fetchAdminOrders, updateOrderStatus } from '../../services/admin'

export default function OrderManagement(){
  const [orders, setOrders] = useState<any[]>([])
  const [meta, setMeta] = useState<any>({})
  const [page, setPage] = useState(1)

  const load = async (p=1)=>{
    try{
      const res = await fetchAdminOrders(p,20,'')
      setOrders(res.items || [])
      setMeta(res.meta || {})
    }catch(err){ console.error(err) }
  }

  useEffect(()=>{ load(page) }, [page])

  const changeStatus = async (id:number)=>{
    const next = prompt('Enter new status (New, Contacted, In Progress, Completed)')
    if(!next) return
    const note = prompt('Optional note') || ''
    try{
      await updateOrderStatus(id, next, note)
      load(page)
    }catch(err){ console.error(err) }
  }

  return (
    <div>
      <h2>Orders</h2>
      <ul>
        {orders.map(o=> (
          <li key={o.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div><strong>{o.order_code}</strong> — {o.service}</div>
            <div>{o.client_name} • {o.phone}</div>
            <div>Status: {o.status}</div>
            <div>Fee: ₹{o.fee_inr}</div>
            <div><button onClick={()=>changeStatus(o.id)}>Change status</button></div>
          </li>
        ))}
      </ul>
      <div style={{display:'flex',gap:8}}>
        <button onClick={()=>setPage(Math.max(1,page-1))}>Prev</button>
        <div>Page {meta.page ?? 1} / {meta.pages ?? 1}</div>
        <button onClick={()=>setPage((meta.page||1)+1)}>Next</button>
      </div>
    </div>
  )
}
