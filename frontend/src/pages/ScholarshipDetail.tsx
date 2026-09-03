import React,{useEffect,useState} from 'react'
import {Link,useParams} from 'react-router-dom'
import Seo from '../components/ui/Seo'
import {fetchScholarship,Scholarship} from '../services/scholarships'

export default function ScholarshipDetail(){
 const {slug=''}=useParams(),[item,setItem]=useState<Scholarship|null>(null),[error,setError]=useState('')
 useEffect(()=>{let active=true;fetchScholarship(slug).then(value=>active&&setItem(value)).catch(e=>active&&setError(e instanceof Error?e.message:'Scholarship unavailable'));return()=>{active=false}},[slug])
 if(error)return <div className="empty-dashboard"><h1>Scholarship unavailable</h1><p>{error}</p><Link to="/scholarships">View active scholarships</Link></div>
 if(!item)return <div className="jobs-loading" role="status"><div className="loading-dot"/><p>Loading scholarship…</p></div>
 const apply=`/services/scholarship-application-assistance?scholarship=${encodeURIComponent(item.slug)}`
 return <article className="content-section"><Seo title={item.title} description={`${item.provider} scholarship eligibility, deadline and application assistance.`} path={`/scholarships/${item.slug}`} index/>
   <span className="eyebrow">{item.source_name}</span><h1>{item.title}</h1><p><strong>Provider:</strong> {item.provider}</p>{item.award&&<p><strong>Award:</strong> {item.award}</p>}{item.region&&<p><strong>Region:</strong> {item.region}</p>}{item.education_level&&<p><strong>Study level:</strong> {item.education_level}</p>}{item.category&&<p><strong>Category:</strong> {item.category}</p>}<h2>Eligibility</h2><p>{item.eligibility||'Review the current scholarship notice for complete eligibility criteria.'}</p><p><strong>Application deadline:</strong> {item.deadline?new Date(`${item.deadline}T00:00:00`).toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}):'See current scholarship listing'}</p>
   <div className="button-row"><a className="btn btn-secondary" href={item.source_url} target="_blank" rel="noreferrer">Source details</a><a className="btn btn-secondary" href={item.application_url} target="_blank" rel="noreferrer">Official / partner application</a><Link className="btn btn-primary" to={apply}>Get Application Assistance</Link></div>
   <p className="muted">Our payment is for application assistance only. Scholarship awards and eligibility are determined by the scholarship provider.</p>
 </article>
}
