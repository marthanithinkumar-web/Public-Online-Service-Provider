import React,{useEffect,useMemo,useState} from 'react'
import {Link} from 'react-router-dom'
import {fetchJobs,JobNotification} from '../../services/jobs'
import JobCard from './JobCard'

export default function JobRecommendations({profile}:{profile:any}){
  const [jobs,setJobs]=useState<JobNotification[]>([]);const [loading,setLoading]=useState(true)
  useEffect(()=>{let active=true;fetchJobs({limit:20}).then(data=>{if(active)setJobs(data.items||[])}).catch(()=>{}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[])
  const suggested=useMemo(()=>{
    const details=profile?.service_profile||{}
    const terms=[details.education_qualification,details.district,details.state,details.occupation].filter(Boolean).map((value:string)=>value.toLowerCase())
    return [...jobs].sort((a,b)=>{const score=(job:JobNotification)=>terms.reduce((total,term)=>total+(`${job.qualification||''} ${job.location||''} ${job.title}`.toLowerCase().includes(term)?1:0),0);return score(b)-score(a)}).slice(0,3)
  },[jobs,profile])
  return <section className="dashboard-section client-job-suggestions"><div className="section-header inline"><div><span className="eyebrow">Updated daily</span><h2>Job opportunities you may want to review</h2><p>Suggestions use any optional profile details you entered. Final eligibility is always decided by the official organization.</p></div><Link className="text-link" to="/jobs">View all jobs →</Link></div>{loading?<div className="jobs-loading"><div className="loading-dot"/><p>Loading verified notices…</p></div>:suggested.length?<div className="client-job-list">{suggested.map(job=><JobCard key={job.id} job={job}/>)}</div>:<div className="empty-dashboard"><h3>No published notices yet</h3><p>Incomplete notices remain hidden until they are checked.</p></div>}</section>
}
