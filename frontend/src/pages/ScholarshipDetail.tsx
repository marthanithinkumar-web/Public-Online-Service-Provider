import React,{useEffect,useMemo,useState} from 'react'
import {Link,useParams} from 'react-router-dom'
import Seo,{SITE} from '../components/ui/Seo'
import {fetchScholarship,Scholarship,scholarshipSourceLabel} from '../services/scholarships'

const genericEligibility=(value?:string|null)=>!value||/apply only if|review the current|official provider|complete eligibility/i.test(value)
function criteria(item:Scholarship){
 const raw=genericEligibility(item.eligibility)?'':String(item.eligibility||'')
 const parts=raw.split(/\n|;|•|\.(?=\s+[A-Z])/).map(x=>x.trim()).filter(x=>x.length>3)
 if(parts.length)return parts
 const out:string[]=[]
 if(item.education_level)out.push(`Study level: ${item.education_level}`)
 if(item.region)out.push(`Region: ${item.region}`)
 if(item.category)out.push(`Category: ${item.category}`)
 if(item.academic_year)out.push(`Academic year: ${item.academic_year}`)
 out.push('Meet the current scheme-specific conditions in the linked official notification before submission.')
 return out
}

export default function ScholarshipDetail(){
 const {slug=''}=useParams(),[item,setItem]=useState<Scholarship|null>(null),[error,setError]=useState('')
 useEffect(()=>{let active=true;fetchScholarship(slug).then(value=>active&&setItem(value)).catch(e=>active&&setError(e instanceof Error?e.message:'Scholarship unavailable'));return()=>{active=false}},[slug])
 const eligibility=useMemo(()=>item?criteria(item):[],[item])
 if(error)return <div className="empty-dashboard"><h1>Scholarship unavailable</h1><p>{error}</p><Link to="/scholarships">View active scholarships</Link></div>
 if(!item)return <div className="jobs-loading" role="status"><div className="loading-dot"/><p>Loading scholarship…</p></div>
 const official=item.is_official||item.source_type==='official'
 const apply=`/services/scholarship-application-assistance?scholarship=${encodeURIComponent(item.slug)}`
 const description=`${item.provider} scholarship eligibility, deadline and application assistance.`
 const schema={'@context':'https://schema.org','@type':'WebPage',name:item.title,url:`${SITE.url}/scholarships/${item.slug}`,description,isPartOf:{'@type':'WebSite',name:SITE.name,url:SITE.url}}
 return <article className="content-section"><Seo title={item.title} description={description} path={`/scholarships/${item.slug}`} index schema={schema}/>
   <span className="eyebrow">{scholarshipSourceLabel(item)}{item.stale_source?' · source check delayed':''}</span><h1>{item.title}</h1><p><strong>Provider:</strong> {item.provider}</p>{item.award&&<p><strong>Award:</strong> {item.award}</p>}{item.region&&<p><strong>Region:</strong> {item.region}</p>}{item.education_level&&<p><strong>Study level:</strong> {item.education_level}</p>}{item.academic_year&&<p><strong>Academic year:</strong> {item.academic_year}</p>}{item.category&&<p><strong>Category:</strong> {item.category}</p>}
   <h2>Eligibility</h2><ul>{eligibility.map((x,i)=><li key={i}>{x}</li>)}</ul><p className="muted">Eligibility shown here is a client-friendly summary of the verified listing data. The linked official notification remains authoritative where a condition is not supplied in the source feed.</p><p><strong>Application deadline:</strong> {item.deadline?new Date(`${item.deadline}T00:00:00`).toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'}):'See current scholarship listing'}</p>
   <div className="button-row"><a className="btn btn-secondary" href={item.source_url} target="_blank" rel="noreferrer">{official?'Official source details':'Partner source details'}</a><a className="btn btn-secondary" href={item.application_url} target="_blank" rel="noreferrer">{official?'Official application':'Partner application'}</a><Link className="btn btn-primary" to={apply}>Apply with Assistance</Link></div>
   <p className="muted">Our payment is for application assistance only. Scholarship awards and eligibility are determined by the scholarship provider. {official?'This listing was discovered from an allow-listed government source.':'This is a private or partner listing and is not presented as a government scholarship source.'}</p>
 </article>
}
