import React, { useEffect, useState } from 'react'
import { fetchAdminOrders } from '../../services/admin'

export default function AdminDashboard(){
  const [meta, setMeta] = useState<any>({})
  const [counts, setCounts] = useState<any>({})

  useEffect(()=>{
    const load = async ()=>{
      try{
        const totalRes = await fetchAdminOrders(1,1,'')
        setMeta(totalRes.meta || {})
        const statuses = ['New','Contacted','In Progress','Completed']
        const c:any = {}
        for(const s of statuses){
          const r = await fetchAdminOrders(1,1,s)
          c[s] = r.meta ? r.meta.total : 0
        }
        setCounts(c)
      }catch(err){
        console.error(err)
      }
    }
    load()
  }, [])

  return (
    <div>
      <h2>Dashboard</h2>
      <div style={{display:'flex',gap:12,flexWrap:'wrap'}}>
        <div style={{padding:12,background:'#fff',borderRadius:6,boxShadow:'0 1px 3px rgba(0,0,0,0.08)'}}>Total Orders<br/><strong>{meta.total ?? 0}</strong></div>
        <div style={{padding:12,background:'#fff',borderRadius:6}}>New<br/><strong>{counts['New'] ?? 0}</strong></div>
        <div style={{padding:12,background:'#fff',borderRadius:6}}>In Progress<br/><strong>{counts['In Progress'] ?? 0}</strong></div>
        <div style={{padding:12,background:'#fff',borderRadius:6}}>Completed<br/><strong>{counts['Completed'] ?? 0}</strong></div>
      </div>
    </div>
  )
}
