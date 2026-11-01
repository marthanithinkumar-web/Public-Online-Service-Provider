import React,{FormEvent,useEffect,useState} from 'react'
import {useSearchParams} from 'react-router-dom'
import {fetchJobs,fetchJobSources,JobNotification,JobSource} from '../services/jobs'
import JobCard from '../components/jobs/JobCard'

const PAGE_SIZE=12

export default function Jobs(){
  const [params,setParams]=useSearchParams()
  const [jobs,setJobs]=useState<JobNotification[]>([])
  const [sources,setSources]=useState<JobSource[]>([])
  const [total,setTotal]=useState(0)
  const [query,setQuery]=useState(params.get('q')||'')
  const [location,setLocation]=useState(params.get('location')||params.get('state')||'')
  const [qualification,setQualification]=useState(params.get('qualification')||params.get('education')||'')
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')
  const [retryCount,setRetryCount]=useState(0)
  const type=params.get('type')||''
  const featured=params.get('featured')==='true'
  const deadline=params.get('deadline')||''
  const sort=params.get('sort')||'deadline_asc'
  const page=Math.max(1,Number(params.get('page')||1)||1)
  const submitted=params.get('q')||''

  const updateFilters=(updates:Record<string,string>)=>{
    const next=new URLSearchParams(params)
    for(const [key,value] of Object.entries(updates)){
      if(value)next.set(key,value)
      else next.delete(key)
    }
    next.set('page','1')
    setParams(next,{replace:true})
  }

  useEffect(()=>{
    let active=true
    setLoading(true)
    setError('')
    fetchJobs({
      limit:PAGE_SIZE,
      page,
      q:submitted,
      type,
      featured,
      location:params.get('location')||params.get('state')||'',
      qualification:params.get('qualification')||params.get('education')||'',
      deadline,
      sort,
    }).then(data=>{
      if(!active)return
      setJobs(data.items||[])
      setTotal(data.total??data.count??0)
    }).catch(()=>active&&setError('We could not load the verified job feed. Please try again.')).finally(()=>active&&setLoading(false))
    return ()=>{active=false}
  },[submitted,type,featured,deadline,sort,page,params,retryCount])

  useEffect(()=>{fetchJobSources().then(data=>setSources(data.items||[])).catch(()=>{})},[])

  const submit=(event:FormEvent)=>{
    event.preventDefault()
    const next=new URLSearchParams(params)
    for(const [key,value] of [['q',query.trim()],['location',location.trim()],['qualification',qualification.trim()]] as const){
      if(value)next.set(key,value)
      else next.delete(key)
    }
    next.delete('state')
    next.delete('education')
    next.set('page','1')
    setParams(next,{replace:true})
  }

  const clearFilters=()=>{
    setQuery('')
    setLocation('')
    setQualification('')
    setParams({}, {replace:true})
  }
  const movePage=(nextPage:number)=>{
    const next=new URLSearchParams(params.toString())
    next.set('page',String(nextPage))
    setParams(next)
  }

  return <div className="jobs-page">
    <section className="jobs-hero">
      <span className="eyebrow light">Jobs &amp; opportunities</span>
      <h1>Verified recruitment notices from official sources</h1>
      <p>Search government and private opportunities gathered from approved official portals. Unclear details are held for review, never guessed.</p>
      <form className="jobs-search" onSubmit={submit}>
        <label className="visually-hidden" htmlFor="job-search">Search job notices</label>
        <input id="job-search" type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search title, organization or keywords"/>
        <label className="visually-hidden" htmlFor="job-location">Filter by state or location</label>
        <input id="job-location" type="search" value={location} onChange={event=>setLocation(event.target.value)} placeholder="State or location"/>
        <label className="visually-hidden" htmlFor="job-qualification">Filter by qualification or education</label>
        <input id="job-qualification" type="search" value={qualification} onChange={event=>setQualification(event.target.value)} placeholder="Qualification or education"/>
        <button type="submit">Apply filters</button>
      </form>
      <div className="jobs-trust-row"><span>✓ Official links only</span><span>✓ Updated daily</span><span>✓ No OTP, PIN or password requested</span></div>
    </section>
    <section className="jobs-directory" aria-labelledby="jobs-directory-title">
      <div className="section-header inline">
        <div>
          <span className="eyebrow">Opportunity directory</span>
          <h2 id="jobs-directory-title">Current published notices</h2>
          {!loading&&!error&&<p className="job-results-summary" role="status">{total} verified notice{total===1?'':'s'}{submitted?` matching “${submitted}”`:''}</p>}
        </div>
        <div className="job-filter-tabs" role="group" aria-label="Filter jobs by type">
          <button type="button" className={!type?'active':''} onClick={()=>updateFilters({type:''})} aria-pressed={!type}>All</button>
          <button type="button" className={type==='government'?'active':''} onClick={()=>updateFilters({type:'government'})} aria-pressed={type==='government'}>Government</button>
          <button type="button" className={type==='private'?'active':''} onClick={()=>updateFilters({type:'private'})} aria-pressed={type==='private'}>Private</button>
        </div>
      </div>
      <div className="job-filter-tabs" role="group" aria-label="Additional job filters">
        <label><input type="checkbox" checked={featured} onChange={event=>updateFilters({featured:event.target.checked?'true':''})}/> Featured only</label>
        <label>Deadline <select value={deadline} onChange={event=>updateFilters({deadline:event.target.value})}>
          <option value="">Any current deadline</option><option value="closing_soon">Closing within 7 days</option><option value="this_month">Closing this month</option>
        </select></label>
        <label>Sort <select value={sort} onChange={event=>updateFilters({sort:event.target.value})}>
          <option value="deadline_asc">Soonest deadline</option><option value="deadline_desc">Latest deadline</option><option value="newest">Recently published</option>
        </select></label>
        <button type="button" onClick={clearFilters}>Clear filters</button>
      </div>
      {loading&&<div className="dashboard-state"><div className="loading-dot"/><p>Loading current notices…</p></div>}
      {error&&<div className="dashboard-state error-state" role="alert"><p>{error}</p><button onClick={()=>setRetryCount(value=>value+1)}>Try again</button></div>}
      {!loading&&!error&&!jobs.length&&<div className="empty-dashboard"><h3>No matching published notices</h3><p>Try broader keywords, a different location, or clear some filters. Notices with incomplete or uncertain data remain in administrator review.</p></div>}
      <div className="jobs-list">{jobs.map(job=><JobCard key={job.id} job={job}/>)}</div>
      {!loading&&!error&&total>PAGE_SIZE&&<nav className="job-pagination" aria-label="Job result pages">
        <button type="button" disabled={page<=1} onClick={()=>movePage(page-1)}>Previous</button>
        <span>Page {page} of {Math.ceil(total/PAGE_SIZE)}</span>
        <button type="button" disabled={page>=Math.ceil(total/PAGE_SIZE)} onClick={()=>movePage(page+1)}>Next</button>
      </nav>}
    </section>
    <section className="job-source-transparency"><div><span className="eyebrow">Source transparency</span><h2>Approved official sources</h2><p>The official boards are checked automatically every day at about 7:45 AM IST. New notices appear after source, duplicate, date and completeness checks; unclear details are never guessed.</p><p>This independent website links to source organizations; it does not represent them. Always confirm eligibility, fees and deadlines in the official notice.</p></div><div className="source-chip-list">{sources.map(source=><a key={source.key} href={source.listing_url} target="_blank" rel="noopener noreferrer"><span className={`source-status ${source.last_sync_status==='success'?'healthy':''}`}/><strong>{source.name}</strong><small>{source.last_sync_completed_at?`Last checked ${new Date(source.last_sync_completed_at).toLocaleString('en-IN')}`:'Scheduled for daily checks'}</small></a>)}</div></section>
  </div>
}
