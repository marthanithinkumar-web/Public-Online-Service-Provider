import React,{useEffect,useMemo,useState} from 'react'
import {Link,useNavigate,useParams} from 'react-router-dom'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {getSession} from '../services/session'
import {getToken,getUser} from '../services/localStorage'
import {fetchClientProfile} from '../services/auth'
import FeeSummary from '../components/ui/FeeSummary'

type Step=1|2|3|4
type Field={key:string;label:string;placeholder?:string;type?:'text'|'date';required?:boolean}
const SERVICE_TIMEOUT_MS=15000
const apiErrorMessage=(value:any,fallback:string)=>typeof value==='string'?value:Object.values(value||{}).flat().join(' ')||fallback

export default function ServiceDetail(){
 const {id}=useParams();const navigate=useNavigate();const session=getSession();const user=getUser()
 const [service,setService]=useState<any>(null);const [loading,setLoading]=useState(true);const [step,setStep]=useState<Step>(1)
 const [form,setForm]=useState({client_name:'',phone:'',email:'',notes:''});const [answers,setAnswers]=useState<Record<string,string>>({});const [file,setFile]=useState<File|null>(null);const [message,setMessage]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [uploadMsg,setUploadMsg]=useState('');const [lastOrder,setLastOrder]=useState<any>(null);const [feeAccepted,setFeeAccepted]=useState(false)

 useEffect(()=>{let active=true;if(!id)return;setLoading(true);setError('');axios.get(`${apiBase}/services/${id}`,{timeout:SERVICE_TIMEOUT_MS}).then(r=>{if(active)setService(r.data)}).catch((e:any)=>{if(active)setError(e?.code==='ECONNABORTED'?'The service server took too long to respond. Please try again.':'Unable to load this service right now.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[id])
 useEffect(()=>{if(!session||session.is_admin)return;const apply=(profile:any)=>setForm(current=>({...current,client_name:profile?.name||current.client_name,phone:profile?.phone||current.phone,email:profile?.email||current.email}));if(user)apply(user);fetchClientProfile().then(result=>apply(result.user)).catch(()=>{if(!user?.name||!user?.phone)setError('Unable to load your contact details. Open Account Settings and confirm your profile.')})},[session?.user_id])

 const requirements=service?.requirements||{fields:[],documents:[],safety_note:'Never provide OTPs, passwords, PINs, CVV, banking credentials, or account recovery codes.'}
 const fields=useMemo<Field[]>(()=>requirements.fields||[],[requirements])
 const serviceQuestions=useMemo(()=>service?.description||'Complete the service-specific information below. The provider will review your request and contact you if anything else is required.',[service])
 const updateAnswer=(key:string,value:string)=>setAnswers(a=>({...a,[key]:value}))
 const validateFields=()=>fields.filter(f=>f.required&&!String(answers[f.key]||'').trim()).map(f=>f.label)
 const submit=async()=>{setError('');setMessage('');setBusy(true);try{const application_data={...answers,request_notes:form.notes.trim(),service_name:service.name};const r=await axios.post(`${apiBase}/orders/`,{service_id:Number(id),application_data},{headers:{Authorization:`Bearer ${getToken()}`},timeout:SERVICE_TIMEOUT_MS});setLastOrder(r.data.order);setMessage(r.data.message);setStep(4)}catch(err:any){setError(err?.code==='ECONNABORTED'?'Submission timed out. Please try again.':apiErrorMessage(err?.response?.data?.error,'Unable to submit your request. Please try again.'))}finally{setBusy(false)}}
 const uploadFile=async(e:React.FormEvent)=>{e.preventDefault();if(!file||!lastOrder)return;setUploadMsg('Uploading…');try{const fd=new FormData();fd.append('file',file);fd.append('order_id',String(lastOrder.id));const r=await axios.post(`${apiBase}/uploads/`,fd,{headers:{Authorization:`Bearer ${getToken()}`},timeout:30000});setUploadMsg(r.data.message);setFile(null)}catch(err:any){setUploadMsg(err?.code==='ECONNABORTED'?'Upload timed out. Please try again.':apiErrorMessage(err?.response?.data?.error,'Upload failed. Please try again.'))}}
 const returnTo=encodeURIComponent(`/service/${id}`)

 if(loading)return <div className="empty-state">Loading service details…</div>
 if(!service)return <div className="empty-state"><h2>Service unavailable</h2><p>{error||'We could not find this service.'}</p><button className="btn btn-secondary" onClick={()=>window.location.reload()}>Try again</button><Link className="btn btn-primary" to="/">Return home</Link></div>
 if(!session)return <div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Ready to request this service?</h2><p>Browse service information without signing in. When you choose to request it, we’ll securely take you to sign in or create an account, then return you directly to this application.</p><div className="cta-row"><Link className="btn btn-primary" to={`/login?returnTo=${returnTo}`}>Sign in & continue</Link><Link className="btn btn-secondary" to={`/register?returnTo=${returnTo}`}>Create account</Link></div></section></div>
 if(session.is_admin)return <div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Client requests only</h2><p>Admin accounts manage incoming requests from the admin dashboard. Please use a client account to submit a service request.</p><Link className="btn btn-primary" to="/admin/dashboard">Go to admin dashboard</Link></section></div>

 return <div className="service-detail-page">
  <div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><FeeSummary data={service}/></div>
  <div className="request-steps" aria-label="Request progress"><span className={step>=1?'active':''}>1. Contact</span><span className={step>=2?'active':''}>2. Application</span><span className={step>=3?'active':''}>3. Review</span><span className={step>=4?'active':''}>4. Submitted</span></div>
  {error&&<p className="info" role="alert">{error}</p>}
  {step===1&&<section className="dashboard-section request-form"><span className="eyebrow">Step 1</span><h2>Confirm your contact details</h2><p>Your signed-in account details are pre-filled. Check them and continue.</p><label>Full name<input value={form.client_name} onChange={e=>setForm({...form,client_name:e.target.value})} required/></label><label>Phone<input type="tel" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} required/></label><label>Email<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><button type="button" onClick={()=>{if(form.client_name.trim().length<2||form.phone.trim().length<7){setError('Please complete your name and phone number in Account Settings.');return}setError('');setStep(2)}}>Continue</button></section>}
  {step===2&&<section className="dashboard-section request-form">
    <span className="eyebrow">Step 2</span><h2>Complete the application</h2><p>{serviceQuestions}</p>
    <div className="trust-note"><strong>Privacy:</strong> {requirements.safety_note}</div>
    {fields.map(field=><label key={field.key}>{field.label}<input type={field.type||'text'} placeholder={field.placeholder} value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)} required={field.required}/></label>)}
    {requirements.documents?.length>0&&<div className="document-checklist"><h3>Documents you may need</h3><ul>{requirements.documents.map((document:string)=><li key={document}>{document}</li>)}</ul><p>Documents can be uploaded after the request is created or when the provider asks for them.</p></div>}
    <label>Additional instructions / notes<textarea rows={6} value={form.notes} onChange={event=>setForm({...form,notes:event.target.value})} placeholder="Add deadlines or other relevant information…"/></label>
    <FeeSummary data={service} compact={true}/>
    <div className="cta-row"><button type="button" className="btn btn-secondary" onClick={()=>setStep(1)}>Back</button><button type="button" onClick={()=>{const missing=validateFields();if(missing.length){setError(`Please complete: ${missing.join(', ')}`);return}setError('');setStep(3)}}>Review application</button></div>
  </section>}
  {step===3&&<section className="dashboard-section"><span className="eyebrow">Step 3</span><h2>Review before submitting</h2><div className="request-summary"><p><strong>Service:</strong> {service.name}</p><p><strong>Name:</strong> {form.client_name}</p><p><strong>Phone:</strong> {form.phone}</p><p><strong>Email:</strong> {form.email||'Not provided'}</p>{fields.map(f=><p key={f.key}><strong>{f.label}:</strong> {answers[f.key]||'—'}</p>)}<p><strong>Additional notes:</strong> {form.notes||'None'}</p></div><FeeSummary data={service}/><label className="fee-acknowledgement"><input type="checkbox" checked={feeAccepted} onChange={e=>setFeeAccepted(e.target.checked)}/> I understand that the assistance fee is separate from any government or official fee.</label><div className="cta-row"><button type="button" className="btn btn-secondary" onClick={()=>setStep(2)}>Edit application</button><button type="button" disabled={busy||!feeAccepted} onClick={submit}>{busy?'Submitting…':'Confirm & submit request'}</button></div></section>}
  {step===4&&<section className="dashboard-section"><span className="eyebrow">Request submitted</span><h2>We received your request</h2><p className="success-message">{message}</p><div className="request-confirmation"><strong>Request ID</strong><div>{lastOrder?.order_code}</div><p>Status: <strong>{lastOrder?.status||'Submitted'}</strong></p></div><FeeSummary data={lastOrder||service}/><div className="upload-card"><h3>Upload supporting documents</h3><p>Upload documents relevant to this request. Maximum 10 MB per document.</p><form onSubmit={uploadFile}><input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>{const selected=e.target.files?.[0]||null;if(selected&&selected.size>10*1024*1024){setUploadMsg('Please choose a file smaller than 10 MB.');return}setFile(selected)}}/><button type="submit" disabled={!file}>Upload document</button></form>{uploadMsg&&<p className="info" role="status">{uploadMsg}</p>}</div><div className="cta-row"><button type="button" onClick={()=>navigate('/my-orders')}>Track my request</button><Link className="btn btn-secondary" to="/">Find another service</Link></div></section>}
 </div>
}
