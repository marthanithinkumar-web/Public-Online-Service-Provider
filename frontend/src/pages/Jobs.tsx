import React,{FormEvent,useEffect,useState} from 'react'
import {useSearchParams} from 'react-router-dom'
import {fetchJobs,fetchJobSources,jobApplicationStatus,JobNotification,JobSource} from '../services/jobs'
import JobCard from '../components/jobs/JobCard'

type SortOrder='priority'|'deadline_soonest'|'newest'

export default function Jobs(){
  const [params,setParams]=useSearchParams()
  const initialQuery=params.get('q')||''
  const initialType=['government','private'].includes(params.get('type')||'')?(params.get('type')||''):''
  const initialLocation=params.get('location')||''
  const initialQualification=params.get('qualification')||''
  const initialSort=(['priority','deadline_soonest','newest'].includes(params.get('sort')||'')?params.get('sort'):'priority') as SortOrder
  const [jobs,setJobs]=useState<JobNotification[]>([])
  const [sources,setSources]=useState<JobSource[]>([])
  const [query,setQuery]=useState(initialQuery)
  const [submitted,setSubmitted]=useState(initialQuery)
  const [type,setTypeState]=useState(initialType)
  const [location,setLocation]=useState(initialLocation)
  const [qualification,setQualification]=useState(initialQualification)
  const [sort,setSort]=useState<SortOrder>(initialSort)
  const [loading,setLoading]=useState(true)
  const [error,setError]=useState('')

  const load=()=>{
    setLoading(true);setError('')
    fetchJobs({limit:100,...(submitted?{q:submitted}:{}),...(type?{type}:{}),...(location?{location}:{}),...(qualification?{qualification}:{})})
      .then(data=>setJobs(data.items||[])).catch(()=>setError('We could not load the verified job feed. Please try again.')).finally(()=>setLoading(false))
  }
  useEffect(load,[submitted,type,location,qualification])
  useEffect(()=>{fetchJobSources().then(data=>setSources(data.items||[])).catch(()=>{})},[])

  const updateLocation=(nextQuery:string,nextType:string,nextLocation=location,nextQualification=qualification,nextSort=sort)=>{
    const next=new URLSearchParams()
    if(nextQuery)next.set('q',nextQuery)
    if(nextType)next.set('type',nextType)
    if(nextLocation)next.set('location',nextLocation)
    if(nextQualification)next.set('qualification',nextQualification)
    if(nextSort!=='priority')next.set('sort',nextSort)
    setParams(next,{replace:true})
  }
  const submit=(event:FormEvent)=>{event.preventDefault();const next=query.trim();setSubmitted(next);updateLocation(next,type)}
  const applyFilters=(event:FormEvent)=>{event.preventDefault();setLocation(location.trim());setQualification(qualification.trim());updateLocation(submitted,type,location.trim(),qualification.trim(),sort)}
  const setType=(next:string)=>{setTypeState(next);updateLocation(submitted,next)}
  const verifiedOpenCount=jobs.filter(job=>jobApplicationStatus(job)==='open').length
  const deadlineTodayCount=jobs.filter(job=>jobApplicationStatus(job)==='deadline_today').length
  const visible=[...jobs].sort((a,b)=>{
    if(sort==='deadline_soonest')return String(a.deadline||'9999').localeCompare(String(b.deadline||'9999'))
    if(sort==='newest')return String(b.published_at||b.issue_date||'').localeCompare(String(a.published_at||a.issue_date||''))
    return Number(b.is_featured)-Number(a.is_featured)||String(a.deadline||'9999').localeCompare(String(b.deadline||'9999'))
  })

  return <div className="jobs-page">
    <section className="jobs-hero"><span className="eyebrow light">Jobs & opportunities</span><h1>Verified recruitment notices from official sources</h1><p>Search government and private opportunities gathered from approved official portals. Unclear details are held for review, never guessed.</p>
      <form className="jobs-search" onSubmit={submit}><label className="visually-hidden" htmlFor="job-search">Search job notices</label><input id="job-search" type="search" value={query} onChange={event=>setQuery(event.target.value)} placeholder="Search title, organization, qualification or location"/><button type="submit">Search jobs</button></form>
      <div className="jobs-trust-row"><span>✓ Official links only</span><span>✓ Updated daily</span><span>✓ No OTP, PIN or password requested</span></div>
    </section>
    <section className="jobs-directory" aria-labelledby="jobs-directory-title"><div className="section-header inline"><div><span className="eyebrow">Opportunity directory</span><h2 id="jobs-directory-title">Current published notices</h2>{!loading&&!error&&<p className="job-results-summary" role="status">{verifiedOpenCount} verified open · {deadlineTodayCount} deadline today{submitted?` · matching “${submitted}”`:''}</p>}</div>
      <div className="job-filter-tabs" role="group" aria-label="Filter jobs by type"><button type="button" className={!type?'active':''} onClick={()=>setType('')} aria-pressed={!type}>All</button><button type="button" className={type==='government'?'active':''} onClick={()=>setType('government')} aria-pressed={type==='government'}>Government</button><button type="button" className={type==='private'?'active':''} onClick={()=>setType('private')} aria-pressed={type==='private'}>Private</button></div></div>
      <form className="jobs-filter-form" onSubmit={applyFilters}><label>Location<input value={location} onChange={event=>setLocation(event.target.value)} placeholder="State or city"/></label><label>Qualification<input value={qualification} onChange={event=>setQualification(event.target.value)} placeholder="Graduate, diploma…"/></label><label>Sort<select value={sort} onChange={event=>{const next=event.target.value as SortOrder;setSort(next);updateLocation(submitted,type,location,qualification,next)}}><option value="priority">Priority and deadline</option><option value="deadline_soonest">Deadline soonest</option><option value="newest">Newest notices</option></select></label><button type="submit">Apply filters</button></form>
      {loading&&<div className="dashboard-state"><div className="loading-dot"/><p>Loading current notices…</p></div>}{error&&<div className="dashboard-state error-state" role="alert"><p>{error}</p><button onClick={load}>Try again</button></div>}{!loading&&!error&&!visible.length&&<div className="empty-dashboard"><h3>No matching published notices</h3><p>Try a broader search. Notices with incomplete or uncertain data remain in administrator review.</p></div>}<div className="jobs-list">{visible.map(job=><JobCard key={job.id} job={job}/>)}</div>
    </section>
    <section className="job-source-transparency"><div><span className="eyebrow">Source transparency</span><h2>Approved official sources</h2><p>The official boards are checked automatically every day at about 7:45 AM IST. New notices appear after source, duplicate, date and completeness checks; unclear details are never guessed.</p><p>This independent website links to source organizations; it does not represent them. Always confirm eligibility, fees and deadlines in the official notice.</p></div><div className="source-chip-list">{sources.map(source=><a key={source.key} href={source.listing_url} target="_blank" rel="noopener noreferrer"><span className={`source-status ${source.last_sync_status==='success'?'healthy':''}`}/><strong>{source.name}</strong><small>{source.last_successful_sync_at?`Last successful check ${new Date(source.last_successful_sync_at).toLocaleString('en-IN')}`:(source.last_sync_completed_at?`Last attempt ${new Date(source.last_sync_completed_at).toLocaleString('en-IN')}`:'Scheduled for daily checks')}{Number(source.consecutive_failures||0)>0?` · ${source.consecutive_failures} consecutive failure(s)`:''}</small></a>)}</div></section>
  </div>
}
