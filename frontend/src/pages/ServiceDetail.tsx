import React,{useEffect,useMemo,useState} from 'react'
import {Link,useNavigate,useParams} from 'react-router-dom'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {getSession} from '../services/session'
import {getToken,getUser} from '../services/localStorage'
import {fetchClientProfile} from '../services/auth'
import FeeSummary from '../components/ui/FeeSummary'
import {PROVIDER} from '../services/config'
import Seo,{SITE} from '../components/ui/Seo'
import {servicePath} from '../services/serviceCatalog'
import RequestFeedback from '../components/ui/RequestFeedback'

type Step=1|2|3
type Field={key:string;label:string;placeholder?:string;type?:'text'|'date'|'select';options?:string[];required?:boolean}
const SERVICE_TIMEOUT_MS=15000
const apiErrorMessage=(value:any,fallback:string)=>typeof value==='string'?value:Object.values(value||{}).flat().join(' ')||fallback

function ServiceInformation({service,requirements}:{service:any,requirements:any}){
 return <section className="service-information" aria-label="Service information">
  <div className="service-info-grid"><article><h3>Details needed</h3><ul>{(requirements.fields||[]).map((field:any)=><li key={field.key}>{field.label}</li>)}</ul></article><article><h3>Documents</h3>{requirements.documents?.length?<ul>{requirements.documents.map((item:string)=><li key={item}>{item}</li>)}</ul>:<p>No document needed now.</p>}</article></div>
  <div className="service-safety-banner"><strong>Never share OTPs, passwords, PINs or banking login details.</strong></div>
 </section>
}

export default function ServiceDetail(){
 const {id,slug}=useParams();const navigate=useNavigate();const session=getSession();const user=getUser()
 const [service,setService]=useState<any>(null);const [loading,setLoading]=useState(true);const [step,setStep]=useState<Step>(1)
 const [form,setForm]=useState({client_name:'',phone:'',email:'',notes:''});const [answers,setAnswers]=useState<Record<string,string>>({});const [files,setFiles]=useState<File[]>([]);const [message,setMessage]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [uploadMsg,setUploadMsg]=useState('');const [lastOrder,setLastOrder]=useState<any>(null);const [feeAccepted,setFeeAccepted]=useState(false);const [requestMode,setRequestMode]=useState<'guided'|'express'>('guided')

 useEffect(()=>{let active=true;if(!id&&!slug)return;setLoading(true);setError('');const endpoint=slug?`${apiBase}/services/by-slug/${encodeURIComponent(slug)}`:`${apiBase}/services/${id}`;axios.get(endpoint,{timeout:SERVICE_TIMEOUT_MS}).then(r=>{if(active)setService(r.data)}).catch((e:any)=>{if(active)setError(e?.code==='ECONNABORTED'?'The service server took too long to respond. Please try again.':'Unable to load this service right now.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[id,slug])
 useEffect(()=>{if(id&&service?.slug)navigate(servicePath(service),{replace:true})},[id,service?.slug,navigate])
 useEffect(()=>{if(!session||session.is_admin)return;const apply=(profile:any)=>setForm(current=>({...current,client_name:profile?.name||current.client_name,phone:profile?.phone||current.phone,email:profile?.email||current.email}));if(user)apply(user);fetchClientProfile().then(result=>apply(result.user)).catch(()=>{if(!user?.name||!user?.phone)setError('Unable to load your contact details. Open Account Settings and confirm your profile.')})},[session?.user_id])

 const requirements=service?.requirements||{fields:[],documents:[],safety_note:'Never provide OTPs, passwords, PINs, CVV, banking credentials, or account recovery codes.'}
 const fields=useMemo<Field[]>(()=>requirements.fields||[],[requirements])
 const updateAnswer=(key:string,value:string)=>setAnswers(a=>({...a,[key]:value}))
 const submit=async()=>{setError('');setMessage('');setUploadMsg('');setBusy(true);try{const application_data={...(requestMode==='guided'?answers:{}),request_notes:requestMode==='guided'?form.notes.trim():'',service_name:service.name,request_mode:requestMode};const r=await axios.post(`${apiBase}/orders/`,{service_id:Number(service.id),application_data},{headers:{Authorization:`Bearer ${getToken()}`},timeout:SERVICE_TIMEOUT_MS});const order=r.data.order;setLastOrder(order);let uploaded=0;for(const selected of files){try{const fd=new FormData();fd.append('file',selected);fd.append('order_id',String(order.id));await axios.post(`${apiBase}/uploads/`,fd,{headers:{Authorization:`Bearer ${getToken()}`},timeout:30000});uploaded+=1}catch{setUploadMsg(`${uploaded} of ${files.length} documents uploaded. You can contact the admin if a document needs to be resent.`);break}}if(files.length&&uploaded===files.length)setUploadMsg(`${uploaded} document${uploaded===1?'':'s'} uploaded securely.`);setMessage(r.data.message);setStep(3)}catch(err:any){setError(err?.code==='ECONNABORTED'?'Submission timed out. Please try again.':apiErrorMessage(err?.response?.data?.error,'Unable to submit your request. Please try again.'))}finally{setBusy(false)}}
 const canonicalPath=service?servicePath(service):`/services/${slug||''}`
 const returnTo=encodeURIComponent(canonicalPath)

 if(loading)return <div className="empty-state">Loading service details…</div>
 if(!service)return <><Seo title="Service unavailable" description="The requested public-service assistance page is unavailable." path={canonicalPath} index={false}/><div className="empty-state"><h2>Service unavailable</h2><p>{error||'We could not find this service.'}</p><button className="btn btn-secondary" onClick={()=>window.location.reload()}>Try again</button><Link className="btn btn-primary" to="/">Return home</Link></div></>
 const seoDescription=`${service.description} Review assistance requirements, fees, documents and the request process.`
 const serviceSchema=[
  {'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:SITE.url},{'@type':'ListItem',position:2,name:service.category||'Services',item:`${SITE.url}/#services`},{'@type':'ListItem',position:3,name:service.name,item:`${SITE.url}${canonicalPath}`}]},
  {'@context':'https://schema.org','@type':'Service',name:service.name,description:service.description,serviceType:service.category||'Public-service application assistance',provider:{'@type':'Organization',name:SITE.name,url:SITE.url},areaServed:{'@type':'Country',name:'India'},url:`${SITE.url}${canonicalPath}`},
 ]
 const seo=<Seo title={service.name} description={seoDescription} path={canonicalPath} type="article" schema={serviceSchema}/>
 if(!session)return <>{seo}<div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div><ServiceInformation service={service} requirements={requirements}/><section className="dashboard-section service-request-cta"><h2>Ready to request this service?</h2><p>Sign in or create an account. After authentication, you will return directly to this service and continue the guided request.</p><div className="cta-row"><Link className="btn btn-primary" to={`/login?returnTo=${returnTo}`}>Sign in & continue</Link><Link className="btn btn-secondary" to={`/register?returnTo=${returnTo}`}>Create account</Link></div></section></div></>
 if(session.is_admin)return <>{seo}<div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Client requests only</h2><p>Admin accounts manage incoming requests from the admin dashboard. Please use a client account to submit a service request.</p><Link className="btn btn-primary" to="/admin/dashboard">Go to admin dashboard</Link></section></div></>

 return <>{seo}<div className="service-detail-page">
 <div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div>
  <div className="request-steps simplified" aria-label="Request progress"><span className={step>=1?'active':''} aria-current={step===1?'step':undefined}>1. Details</span><span className={step>=2?'active':''} aria-current={step===2?'step':undefined}>2. Review</span><span className={step>=3?'active':''} aria-current={step===3?'step':undefined}>3. Submitted</span></div>
  {error&&<p className="info" role="alert">{error}</p>}
  {step===1&&<section className="dashboard-section request-form simplified-request-form">
    <span className="eyebrow">Step 1</span><h2>Request details</h2>
    <div className="request-contact-summary"><div><strong>{form.client_name||'Profile name required'}</strong><span>{form.phone||'Phone required'}{form.email?` · ${form.email}`:''}</span></div><Link to="/account-settings">Edit profile</Link></div>
    {fields.length>0&&<><h3>Service details</h3><p className="request-short-hint">Add what you know. You can leave these blank.</p>{fields.map(field=><label key={field.key}>{field.label}{field.type==='select'?<select value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}><option value="">Select</option>{(field.options||[]).map(option=><option key={option} value={option}>{option}</option>)}</select>:<input type={field.type||'text'} placeholder={field.placeholder} value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}/>}</label>)}</>}
    <label>Notes<textarea rows={3} value={form.notes} onChange={event=>setForm({...form,notes:event.target.value})} placeholder="Short note, if needed"/></label>
    {requirements.documents?.length>0&&<div className="upload-card"><h3>Documents for this service</h3><ul>{requirements.documents.map((item:string)=><li key={item}>{item}</li>)}</ul><label>Upload documents<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={event=>{const selected=Array.from(event.target.files||[]);const oversized=selected.find(item=>item.size>10*1024*1024);if(oversized){setError(`${oversized.name} is larger than 10 MB.`);event.target.value='';return}setError('');setFiles(selected)}}/></label><small>PDF, PNG or JPG · maximum 10 MB each</small>{files.length>0&&<ul className="document-list">{files.map(item=><li key={`${item.name}-${item.lastModified}`}>{item.name}</li>)}</ul>}</div>}
    <p className="request-safety-line">Do not enter OTPs, passwords, PINs or banking details.</p>
    <div className="cta-row"><button type="button" onClick={()=>{if(form.client_name.trim().length<2||form.phone.trim().length<7){setError('Please complete your name and phone number in Account Settings.');return}const hasDetails=Object.values(answers).some(value=>value.trim())||Boolean(form.notes.trim());setRequestMode(hasDetails?'guided':'express');setError('');setStep(2)}}>Review request</button></div>
  </section>}
  {step===2&&<section className="dashboard-section simplified-review"><span className="eyebrow">Step 2</span><h2>Review and submit</h2><div className="request-summary"><p><strong>Service:</strong> {service.name}</p><p><strong>Client:</strong> {form.client_name} · {form.phone}</p>{requestMode==='guided'&&fields.filter(f=>answers[f.key]).map(f=><p key={f.key}><strong>{f.label}:</strong> {answers[f.key]}</p>)}{form.notes&&<p><strong>Notes:</strong> {form.notes}</p>}</div><FeeSummary data={service} compact/><label className="fee-acknowledgement"><input type="checkbox" checked={feeAccepted} onChange={e=>setFeeAccepted(e.target.checked)}/> I agree to the Applicable Assistance Fee shown above. Official fees are separate.</label><div className="cta-row"><button type="button" className="btn btn-secondary" onClick={()=>setStep(1)}>Edit</button><button type="button" disabled={busy||!feeAccepted} onClick={submit}>{busy?'Submitting…':'Submit request'}</button></div></section>}
  {step===3&&<section className="dashboard-section simplified-confirmation"><span className="eyebrow">Submitted</span><h2>We are reviewing your request</h2><p>Expected completion: 5 days to 1 week.</p><p className="success-message">{message}</p><div className="request-confirmation"><strong>Order number</strong><div>{lastOrder?.order_code}</div><p>Status: <strong>{lastOrder?.status||'Submitted'}</strong></p></div>{uploadMsg&&<p className="info" role="status">{uploadMsg}</p>}<div className="request-summary"><p><strong>Admin:</strong> {PROVIDER.name}</p><p><strong>Contact:</strong> <a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></p></div>{lastOrder?.id&&<RequestFeedback fixedOrderId={lastOrder.id}/>}<div className="cta-row"><Link className="btn btn-primary" to="/messages">Chat with Admin</Link><button type="button" className="btn btn-secondary" onClick={()=>navigate('/my-orders')}>Dashboard</button></div></section>}
 </div></>
}
