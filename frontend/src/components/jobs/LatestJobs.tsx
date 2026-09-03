import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import {fetchJobs,JobNotification} from '../../services/jobs'
import JobCard from './JobCard'

export default function LatestJobs(){
  const [jobs,setJobs]=useState<JobNotification[]>([]);const [filter,setFilter]=useState('all');const [loading,setLoading]=useState(true);const [error,setError]=useState('')
  useEffect(()=>{let active=true;fetchJobs({limit:12}).then(data=>{if(active)setJobs(data.items||[])}).catch(()=>{if(active)setError('Latest job notices are temporarily unavailable. Service search remains available below.')} ).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[])
  const visible=useMemo(()=>jobs.filter(job=>filter==='all'||job.job_type===filter).slice(0,4),[jobs,filter])
  return <section className="content-section latest-jobs" aria-labelledby="latest-jobs-title"><div className="section-header jobs-section-heading"><div><span className="section-icon" aria-hidden="true">▣</span><div><span className="eyebrow">Official-source notices</span><h2 id="latest-jobs-title">Latest Jobs & Opportunities</h2></div><span className="updated-badge">Updated daily</span></div><div className="jobs-heading-actions"><div className="job-filter-tabs" role="group" aria-label="Filter latest jobs"><button className={filter==='all'?'active':''} onClick={()=>setFilter('all')}>All</button><button className={filter==='government'?'active':''} onClick={()=>setFilter('government')}>Government</button><button className={filter==='private'?'active':''} onClick={()=>setFilter('private')}>Private</button></div><Link className="text-link" to="/jobs">View all jobs →</Link></div></div>
    {loading&&<div className="jobs-loading" role="status"><div className="loading-dot"/><p>Checking official job sources…</p></div>}
    {error&&<p className="info" role="alert">{error}</p>}
    {!loading&&!error&&visible.length===0&&<div className="empty-dashboard"><h3>No verified notices in this filter yet</h3><p>Unclear or incomplete notices are held for administrator review instead of being shown.</p></div>}
    {visible.length>0&&<div className="latest-job-grid">{visible.map(job=><JobCard key={job.id} job={job} compact/>)}</div>}
  </section>
}
