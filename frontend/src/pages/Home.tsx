import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Link } from 'react-router-dom'

export default function Home(){
  const [q, setQ] = useState('')
  const [results, setResults] = useState<any[]>([])

  useEffect(()=>{
    const source = axios.CancelToken.source()
    const doSearch = async ()=>{
      try{
        const res = await axios.get('/api/services/search', { params: { q }, cancelToken: source.token })
        setResults(res.data)
      }catch(err){
        if(!axios.isCancel(err)) console.error(err)
      }
    }
    // Live search: debounce small delay
    const t = setTimeout(()=>{ doSearch() }, 200)
    return ()=>{ clearTimeout(t); source.cancel() }
  }, [q])

  return (
    <div>
      <section className="hero">
        <h1>Your time matters. Let us help with public-service applications.</h1>
        <p>Quick assistance for certificates, job applications, schemes and more.</p>
        <div className="search-box">
          <input aria-label="Search services" placeholder="Search services (e.g. residence, job, certificate)" value={q} onChange={e=>setQ(e.target.value)} />
        </div>
      </section>

      <section>
        <h2>Search results</h2>
        {results.length===0 && <p>No results</p>}
        <ul className="service-list">
          {results.map(s=> (
            <li key={s.id} className="service-card">
              <h3><Link to={`/service/${s.id}`}>{s.name}</Link></h3>
              <p>{s.description}</p>
              <div className="price">₹{s.price_inr}</div>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
