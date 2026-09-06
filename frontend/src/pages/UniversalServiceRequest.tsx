import React,{useEffect,useMemo,useState} from 'react'
import axios from 'axios'
import {Link,useLocation,useNavigate,useParams} from 'react-router-dom'
import Seo from '../components/ui/Seo'
import FeeSummary from '../components/ui/FeeSummary'
import {apiBase} from '../services/apiBase'
import {fetchClientProfile} from '../services/auth'
import {fetchJob,JobNotification} from '../services/jobs'
import {fetchScholarship,Scholarship} from '../services/scholarships'
import {getToken,getUser} from '../services/localStorage'
import {getSession} from '../services/session'
import {readCachedServices,slugifyServiceName} from '../services/serviceCatalog'

type Field={key:string;label:string;type?:'text'|'date'|'select';options?:string[];placeholder?:string;feeFactor?:boolean}
const TIMEOUT=12000
const FALLBACK_FIELDS:Field[]=[
 {key:'applicant_name',label:'Applicant name',placeholder:'Name as used for this application'},
 {key:'date_of_birth',label:'Date of birth',type:'date'},
 {key:'father_or_guardian_name',label:'Father / mother / guardian name'},
 {key:'address',label:'Current address'},
 {key:'district_state',label:'District / state'},
 {key:'purpose_or_request',label:'Purpose / request details'},
 {key:'reference_number',label:'Existing application / ID / reference number'},
]
const JOB_FIELDS:Field[]=[
 {key:'job_post_preference',label:'Post / preference'},
 {key:'date_of_birth',label:'Date of birth',type:'date'},
 {key:'qualification',label:'Highest / relevant qualification'},
 {key:'marks_or_cgpa',label:'Marks / percentage / CGPA'},
 {key:'exam_region',label:'Exam centre / region / zone preference'},
]
const SCHOLARSHIP_FIELDS:Field[]=[
 {key:'student_name',label:'Student name'},
 {key:'date_of_birth',label:'Date of birth',type:'date'},
 {key:'current_course',label:'Current course / class'},
 {key:'institution_name',label:'School / college / institution'},
 {key:'academic_year',label:'Academic year'},
 {key:'category',label:'Category / community'},
 {key:'family_income',label:'Annual family income'},
 {key:'previous_application_id',label:'Previous scholarship / application ID'},
]

function cachedService(id?:string,slug?:string){
 const normalized=slug?slugifyServiceName(slug):''
 return readCachedServices(true).find((item:any)=>id?String(item.id)===String(id):normalized&&[item.slug,slugifyServiceName(item.name),slugifyServiceName(item.catalog_name||'')].filter(Boolean).includes(normalized))||null
}

export default function UniversalServiceRequest(){
 const {id,slug}=useParams();const location=useLocation();const navigate=useNavigate();const session=getSession();const localUser=getUser();
 const params=new URLSearchParams(location.search);const jobSlug=params.get('job')||'';const scholarshipSlug=params.get('scholarship')||''
 const initial=useMemo(()=>cachedService(id,slug),[id,slug]);const [service,setService]=useState<any>(initial);const [loading,setLoading]=useState(!initial);const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [answers,setAnswers]=useState<Record<string,string>>({});const [notes,setNotes]=useState('');const [files,setFiles]=useState<File[]>([]);const [profile,setProfile]=useState<any>(localUser||null);const [job,setJob]=useState<JobNotification|null>(null);const [scholarship,setScholarship]=useState<Scholarship|null>(null)
 useEffect(()=>{let active=true;if(initial){setService(initial);setLoading(false)}const endpoint=slug?`${apiBase}/services/by-slug/${encodeURIComponent(slug)}`:`${apiBase}/services/${id}`;axios.get(endpoint,{timeout:TIMEOUT}).then(r=>active&&setService(r.data)).catch(()=>{if(active&&!initial)setError('Unable to load this service right now.')}).finally(()=>active&&setLoading(false));return()=>{active=false}},[id,slug])
 useEffect(()=>{if(!session||session.is_admin)return;fetchClientProfile().then(r=>setProfile(r.user)).catch(()=>{})},[session?.user_id])
 useEffect(()=>{let active=true;if(!jobSlug){setJob(null);return()=>{active=false}}fetchJob(jobSlug).then(r=>active&&setJob(r.job)).catch(()=>active&&setError('The selected job notice is unavailable or has closed.'));return()=>{active=false}},[jobSlug])
 useEffect(()=>{let active=true;if(!scholarshipSlug){setScholarship(null);return()=>{active=false}}fetchScholarship(scholarshipSlug).then(r=>active&&setScholarship(r)).catch(()=>active&&setError('The selected scholarship is unavailable or has closed.'));return()=>{active=false}},[scholarshipSlug])
 const requirements=service?.requirements||{}
 const fields=useMemo<Field[]>(()=>{
  const serviceFields=(requirements.fields||[]).map((field:any)=>({key:String(field.key),label:String(field.label||field.key),type:field.type==='date'||field.type==='select'?field.type:'text',options:Array.isArray(field.options)?field.options:undefined,placeholder:field.placeholder,feeFactor:Boolean(field.feeFactor)}))
  const jobFeeFields=(job?.fee_factors||[]).map((factor:any)=>({key:String(factor.key),label:String(factor.label),type:factor.type==='select'||factor.type==='boolean'?'select':'text',options:factor.type==='boolean'?['Yes','No']:(factor.options||[]),feeFactor:true}))
  const source=scholarship?[...SCHOLARSHIP_FIELDS,...serviceFields]:job?[...jobFeeFields,...JOB_FIELDS,...serviceFields]:serviceFields.length?serviceFields:FALLBACK_FIELDS
  return source.filter((field,index,all)=>all.findIndex(other=>other.key===field.key)===index)
 },[service?.id,job?.id,scholarship?.id])
 const title=scholarship?`Apply for ${scholarship.title}`:job?`Apply for ${job.title}`:service?.name||'Service request'
 const submit=async()=>{
  if(!profile?.name||!profile?.phone){setError('Please complete your name and phone number in Account Settings before submitting.');return}
  setBusy(true);setError('')
  try{
   const application_data:any={service_name:service.name,request_mode:'guided',request_notes:notes.trim()}
   fields.forEach(field=>{const value=(answers[field.key]||'').trim();if(value)application_data[field.key]=value;else if(field.feeFactor)application_data[field.key]='Not provided by client'})
   if(job)Object.assign(application_data,{job_slug:job.slug,job_title:job.title,job_organization:job.organization,job_official_notice_url:job.official_notice_url,job_application_url:job.application_url,job_source:job.source?.name||null})
   if(scholarship)Object.assign(application_data,{scholarship_slug:scholarship.slug,scholarship_title:scholarship.title,scholarship_provider:scholarship.provider,scholarship_source:scholarship.source_name,scholarship_source_url:scholarship.source_url,scholarship_application_url:scholarship.application_url,no_official_fee:true})
   const response=await axios.post(`${apiBase}/orders/`,{service_id:Number(service.id),application_data},{headers:{Authorization:`Bearer ${getToken()}`},timeout:TIMEOUT})
   const order=response.data.order
   for(const file of files){const body=new FormData();body.append('file',file);body.append('order_id',String(order.id));await axios.post(`${apiBase}/uploads/`,body,{headers:{Authorization:`Bearer ${getToken()}`},timeout:30000})}
   navigate(`/my-orders/${order.id}`,{replace:true})
  }catch(err:any){setError(err?.response?.data?.error||'Unable to submit this request. Please try again.')}finally{setBusy(false)}
 }
 if(loading)return <div className="jobs-loading" role="status"><div className="loading-dot"/><p>Loading application…</p></div>
 if(!service)return <div className="empty-dashboard"><h1>Service unavailable</h1><p>{error||'This service could not be found.'}</p><Link to="/government-services">Browse services</Link></div>
 const returnTo=encodeURIComponent(`${location.pathname}${location.search}`)
 if(!session)return <div className="service-detail-page"><Seo title={title} description={service.description||'Application assistance request'} path={location.pathname}/><div className="service-detail-hero"><h1>{title}</h1><p>{service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Enter details before payment</h2><p>Sign in first. You will return here to enter the basic application details, submit the request, and then continue to fee payment.</p><div className="cta-row"><Link className="btn btn-primary" to={`/login?returnTo=${returnTo}`}>Client login</Link><Link className="btn btn-secondary" to={`/register?returnTo=${returnTo}`}>Create account</Link></div></section></div>
 if(session.is_admin)return <div className="empty-dashboard"><h1>Client request page</h1><p>Use a client account to submit service applications.</p><Link to="/admin/dashboard">Admin dashboard</Link></div>
 return <div className="service-detail-page"><Seo title={title} description={service.description||'Application assistance request'} path={location.pathname}/><div className="service-detail-hero"><span className="eyebrow">Application details</span><h1>{title}</h1><p>{service.description}</p><FeeSummary data={service}/>{scholarship&&<p className="info">Scholarships have no official application fee in this assistance flow. Only the website assistance fee applies.</p>}</div><section className="dashboard-section request-form simplified-request-form"><h2>Enter basic details</h2><div className="request-contact-summary"><div><strong>{profile?.name}</strong><span>{profile?.phone}{profile?.email?` · ${profile.email}`:''}</span></div><Link to="/account-settings">Edit profile</Link></div>{fields.map(field=><label key={field.key}>{field.label}{field.type==='select'?<select value={answers[field.key]||''} onChange={e=>setAnswers(current=>({...current,[field.key]:e.target.value}))}><option value="">Select</option>{(field.options||[]).map(option=><option key={option} value={option}>{option}</option>)}</select>:<input type={field.type||'text'} value={answers[field.key]||''} placeholder={field.placeholder||''} onChange={e=>setAnswers(current=>({...current,[field.key]:e.target.value}))}/>}</label>)}<label>Additional details<textarea rows={4} value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Add anything that will help us process the application"/></label>{(requirements.documents||[]).length>0&&<div className="upload-card"><h3>Documents</h3><ul>{(requirements.documents||[]).map((item:string)=><li key={item}>{item}</li>)}</ul><label>Upload documents<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={e=>setFiles(Array.from(e.target.files||[]).slice(0,20))}/></label>{files.length>0&&<p>{files.length} file{files.length===1?'':'s'} selected</p>}</div>}<p className="request-safety-line">Do not enter OTPs, passwords, PINs or banking login details. Complete those steps yourself only on the official portal.</p>{error&&<p className="info" role="alert">{typeof error==='string'?error:JSON.stringify(error)}</p>}<button className="btn btn-primary" type="button" disabled={busy} onClick={submit}>{busy?'Submitting…':'Submit application'}</button><p className="request-short-hint">After submission, you will continue to the request page for fee payment and tracking.</p></section></div>
}
