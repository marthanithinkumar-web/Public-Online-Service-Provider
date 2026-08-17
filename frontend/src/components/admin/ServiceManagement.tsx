import React, { useEffect, useState } from 'react'
import { fetchServices, createService, updateService, setServiceActive } from '../../services/admin'

export default function ServiceManagement(){
  const [services, setServices] = useState<any[]>([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [price, setPrice] = useState(0)

  const load = async ()=>{
    try{
      const res = await fetchServices()
      setServices(res)
    }catch(err){ console.error(err) }
  }
  useEffect(()=>{ load() }, [])

  const add = async ()=>{
    try{
      await createService({ name, description: desc, price_inr: price })
      setName(''); setDesc(''); setPrice(0)
      load()
    }catch(err){ console.error(err) }
  }

  const toggle = async (s:any)=>{
    try{
      await setServiceActive(s.id, !s.is_active)
      load()
    }catch(err){ console.error(err) }
  }

  return (
    <div>
      <h2>Service Management</h2>
      <div style={{marginBottom:12}}>
        <input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
        <input placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
        <input type="number" placeholder="Price" value={price} onChange={e=>setPrice(Number(e.target.value))} />
        <button onClick={add}>Add Service</button>
      </div>
      <ul>
        {services.map(s=> (
          <li key={s.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div><strong>{s.name}</strong> — ₹{s.price_inr}</div>
            <div>{s.description}</div>
            <div>Category: {s.category}</div>
            <div>Active: {String(s.is_active)}</div>
            <div><button onClick={()=>toggle(s)}>{s.is_active ? 'Disable' : 'Enable'}</button></div>
          </li>
        ))}
      </ul>
    </div>
  )
}
