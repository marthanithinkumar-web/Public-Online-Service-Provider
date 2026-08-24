import React, { useEffect, useState } from 'react'
import { fetchServices, createService, updateService, setServiceActive } from '../../services/admin'

export default function ServiceManagement(){
  const [services, setServices] = useState<any[]>([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [price, setPrice] = useState(0)
  const [editing,setEditing]=useState<number|null>(null);const [error,setError]=useState('');const [busy,setBusy]=useState(false)

  const load = async ()=>{
    try{
      const res = await fetchServices()
      setServices(res)
    }catch(err){ setError('Unable to load services.') }
  }
  useEffect(()=>{ load() }, [])

  const add = async ()=>{
    try{setBusy(true);setError('')
      if(editing)await updateService(editing,{ name, description: desc, price_inr: price })
      else await createService({ name, description: desc, price_inr: price })
      setName(''); setDesc(''); setPrice(0)
      setEditing(null)
      load()
    }catch(err:any){ setError(err?.response?.data?.error||'Unable to save service.') }finally{setBusy(false)}
  }

  const toggle = async (s:any)=>{
    try{
      await setServiceActive(s.id, !s.is_active)
      load()
    }catch(err){ setError('Unable to update service availability.') }
  }

  return (
    <div>
      <h2>Service Management</h2>
      {error&&<p className="info" role="alert">{error}</p>}<div className="dashboard-section admin-form" style={{marginBottom:12}}>
        <input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
        <input placeholder="Description" value={desc} onChange={e=>setDesc(e.target.value)} />
        <input type="number" placeholder="Price" value={price} onChange={e=>setPrice(Number(e.target.value))} />
        <button disabled={busy||name.trim().length<2} onClick={add}>{busy?'Saving…':editing?'Save changes':'Add service'}</button>{editing&&<button className="btn-secondary" onClick={()=>{setEditing(null);setName('');setDesc('');setPrice(0)}}>Cancel edit</button>}
      </div>
      <ul>
        {services.map(s=> (
          <li key={s.id} style={{border:'1px solid #eee',padding:8,margin:8,borderRadius:6}}>
            <div><strong>{s.name}</strong> — ₹{s.price_inr}</div>
            <div>{s.description}</div>
            <div>Category: {s.category}</div>
            <div>Active: {String(s.is_active)}</div>
            <div className="button-row"><button onClick={()=>{setEditing(s.id);setName(s.name);setDesc(s.description||'');setPrice(s.price_inr||0);window.scrollTo({top:0,behavior:'smooth'})}}>Edit</button><button className="btn-secondary" onClick={()=>toggle(s)}>{s.is_active ? 'Disable' : 'Enable'}</button></div>
          </li>
        ))}
      </ul>
    </div>
  )
}
