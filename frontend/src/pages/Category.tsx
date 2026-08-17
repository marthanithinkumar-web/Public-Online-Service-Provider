import React, { useEffect, useState } from 'react'
import axios from 'axios'
import { Link, useParams } from 'react-router-dom'

export default function Category(){
  const { name } = useParams()
  const [services, setServices] = useState<any[]>([])
  const [title, setTitle] = useState(name || 'Services')

  useEffect(()=>{
    if(!name) return
    const load = async ()=>{
      try{
        // Using search endpoint to match category name and keywords
        const res = await axios.get('/api/services/search', { params: { q: name } })
        setServices(res.data)
        setTitle((name || '').replace('-', ' '))
      }catch(err){ console.error(err) }
    }
    load()
  }, [name])

  return (
    <div>
      <h1 style={{textTransform:'capitalize'}}>{title}</h1>
      <p>Our {title} services — we help you with applications and documents. Contact: <strong>Provider Name</strong> • Phone: 9999999999</p>
      <ul className="service-list">
        {services.map(s=> (
          <li key={s.id} className="service-card">
            <h3><Link to={`/service/${s.id}`}>{s.name}</Link></h3>
            <p>{s.description}</p>
            <div className="price">₹{s.price_inr}</div>
          </li>
        ))}
      </ul>
    </div>
  )
}
