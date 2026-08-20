import React, {useEffect, useMemo, useState} from 'react'
import {Link, useNavigate, useParams} from 'react-router-dom'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {getSession} from '../services/session'
import {getToken, getUser} from '../services/localStorage'

type Step = 1 | 2 | 3 | 4

type Field = { key:string; label:string; placeholder?:string; type?:'text'|'date'; required?:boolean }

export default function ServiceDetail(){
 const {id}=useParams(); const navigate=useNavigate(); const session=getSession(); const user=getUser()
 const [service,setService]=useState<any>(null); const [loading,setLoading]=useState(true); const [step,setStep]=useState<Step>(1)
 const [form,setForm]=useState({client_name:'',phone:'',email:'',notes:''}); const [answers,setAnswers]=useState<Record<string,string>>({})
 const [file,setFile]=useState<File|null>(null); const [message,setMessage]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false); const [uploadMsg,setUploadMsg]=useState(''); const [lastOrder,setLastOrder]=useState<any>(null)

 useEffect(()=>{if(!id)return;axios.get(`${apiBase}/services/${id}`).then(r=>setService(r.data)).catch(()=>setError('Unable to load this service right now.')).finally(()=>setLoading(false))},[id])
 useEffect(()=>{if(session&&!session.is_admin)setForm({client_name:user?.name||'',phone:user?.phone||'',email:user?.email||'',notes:''})},[session?.user_id])

 const text=useMemo(()=>`${service?.name||''} ${service?.keywords||''} ${service?.category||''}`.toLowerCase(),[service])
 const fields=useMemo<Field[]>(()=>{
   if(text.includes('scholarship')||text.includes('epass')) return [
    {key:'application_type',label:'Application type',placeholder:'Fresh or Renewal',required:true},{key:'course_class',label:'Course / Class',required:true},{key:'institution',label:'School / College / Institution',required:true},{key:'academic_year',label:'Academic year',required:true}
   ]
   if(text.includes('poly')||text.includes('eapcet')||text.includes('eamcet')||text.includes('ecet')||text.includes('icet')||text.includes('cet')||text.includes('neet')||text.includes('jee')||text.includes('cuet')||text.includes('exam')) return [
    {key:'qualification',label:'Qualification / Class',required:true},{key:'exam_year',label:'Exam year',required:true},{key:'category',label:'Category (if applicable)'},{key:'application_type',label:'Assistance needed',placeholder:'New application / correction / status',required:true}
   ]
   if(text.includes('aadhaar')||text.includes('aadhar')) return [{key:'update_type',label:'Aadhaar assistance type',placeholder:'Name / address / DOB / mobile / document update',required:true},{key:'deadline',label:'Deadline (if any)',type:'date'}]
   if(text.includes('pan')) return [{key:'application_type',label:'PAN assistance type',placeholder:'New / correction / reprint',required:true},{key:'correction_needed',label:'Correction/details needed'}]
   if(text.includes('voter')) return [{key:'application_type',label:'Voter service type',placeholder:'New registration / correction / address change',required:true},{key:'state',label:'State',required:true}]
   if(text.includes('gurukulam')||text.includes('navodaya')||text.includes('sainik')||text.includes('iiit')||text.includes('admission')) return [{key:'student_class',label:'Student class / year',required:true},{key:'school',label:'Current school / institution'},{key:'admission_type',label:'Admission type',required:true},{key:'deadline',label:'Application deadline (if known)',type:'date'}]
   if(text.includes('certificate')) return [{key:'certificate_type',label:'Certificate type',required:true},{key:'purpose',label:'Purpose of certificate',required:true},{key:'deadline',label:'Deadline (if any)',type:'date'}]
   return [{key:'assistance_type',label:'What assistance do you need?',required:true},{key:'deadline',label:'Deadline (if any)',type:'date'}]
 },[text])

 const serviceQuestions=useMemo(()=>{
   if(text.includes('scholarship')||text.includes('epass')) return 'Provide the student, academic and fresh/renewal information requested below.'
   if(text.includes('exam')||text.includes('cet')||text.includes('neet')||text.includes('jee')) return 'Provide your qualification, exam and application/correction requirements below.'
   if(text.includes('aadhaar')) return 'Tell us the Aadhaar update assistance you need. Never provide OTPs, passwords or PINs.'
   if(text.includes('pan')) return 'Tell us whether you need a new PAN, correction or reprint. Never provide OTPs or passwords.'
   if(text.includes('voter')) return 'Tell us whether this is registration, correction or address/constituency assistance.'
   return 'Complete the service-specific information below and add any important instructions in the notes.'
 },[text])

 const updateAnswer=(key:string,value:string)=>setAnswers(a=>({...a,[key]:value}))
 const validateFields=()=>fields.filter(f=>f.required&&!String(answers[f.key]||'').trim()).map(f=>f.label)
 const submit=async()=>{
   setError('');setMessage('');setBusy(true)
   try{
    const application_data={...answers,request_notes:form.notes.trim(),service_name:service.name}
    const r=await axios.post(`${apiBase}/orders`,{client_name:form.client_name,phone:form.phone,email:form.email,service_id:Number(id),application_data},{headers:{Authorization:`Bearer ${getToken()}`}})
    setLastOrder(r.data.order);setMessage(r.data.message);setStep(4)
   }catch(err:any){setError(err?.response?.data?.error||'Unable to submit your request. Please try again.')}finally{setBusy(false)}
 }
 const uploadFile=async(e:React.FormEvent)=>{e.preventDefault();if(!file||!lastOrder)return;setUploadMsg('Uploading…');try{const fd=new FormData();fd.append('file',file);fd.append('order_id',String(lastOrder.id));const r=await axios.post(`${apiBase}/uploads`,fd,{headers:{Authorization:`Bearer ${getToken()}`}});setUploadMsg(r.data.message);setFile(null)}catch(err:any){setUploadMsg(err?.response?.data?.error||'Upload failed. Please try again.')}}

 if(loading)return <div className="empty-state">Loading service details…</div>
 if(!service)return <div className="empty-state"><h2>Service unavailable</h2><p>{error||'We could not find this service.'}</p><Link className="btn btn-primary" to="/">Return home</Link></div>
 if(!session||session.is_admin)return <div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p></div><section className="dashboard-section"><h2>Client account required</h2><p>Create or sign in to a client account to request this service and securely track documents and progress.</p><Link className="btn btn-primary" to="/login">Login to request</Link><Link className="text-link" to="/register">Create an account →</Link></section></div>

 return <div className="service-detail-page">
  <div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><div className="service-detail-meta"><span>Assistance fee <strong>₹{service.price_inr}</strong></span><span>Official fees, if any, are separate</span></div></div>
  <div className="request-steps" aria-label="Request progress"><span className={step>=1?'active':''}>1. Contact</span><span className={step>=2?'active':''}>2. Application</span><span className={step>=3?'active':''}>3. Review</span><span className={step>=4?'active':''}>4. Submitted</span></div>
  {error&&<p className="info" role="alert">{error}</p>}
  {step===1&&<section className="dashboard-section request-form"><span className="eyebrow">Step 1</span><h2>Confirm your contact details</h2><p>These details come from your client account and will be attached to this request.</p><label>Full name<input value={form.client_name} onChange={e=>setForm({...form,client_name:e.target.value})} required/></label><label>Phone<input type="tel" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} required/></label><label>Email<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><button onClick={()=>{if(form.client_name.trim().length<2||form.phone.trim().length<7){setError('Please complete your name and phone number in Account Settings.');return}setError('');setStep(2)}}>Continue</button></section>}
  {step===2&&<section className="dashboard-section request-form"><span className="eyebrow">Step 2</span><h2>Complete the application</h2><p>{serviceQuestions}</p><div className="trust-note"><strong>Privacy:</strong> Never enter OTPs, passwords, PINs or bank details.</div>{fields.map(f=><label key={f.key}>{f.label}<input type={f.type||'text'} placeholder={f.placeholder} value={answers[f.key]||''} onChange={e=>updateAnswer(f.key,e.target.value)} required={f.required}/></label>)}<label>Additional instructions / notes<textarea rows={6} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} placeholder="Add deadlines or other relevant information…"/></label><div className="cta-row"><button className="btn btn-secondary" onClick={()=>setStep(1)}>Back</button><button onClick={()=>{const missing=validateFields();if(missing.length){setError(`Please complete: ${missing.join(', ')}`);return}setError('');setStep(3)}}>Review application</button></div></section>}
  {step===3&&<section className="dashboard-section"><span className="eyebrow">Step 3</span><h2>Review before submitting</h2><div className="request-summary"><p><strong>Service:</strong> {service.name}</p><p><strong>Name:</strong> {form.client_name}</p><p><strong>Phone:</strong> {form.phone}</p><p><strong>Email:</strong> {form.email||'Not provided'}</p>{fields.map(f=><p key={f.key}><strong>{f.label}:</strong> {answers[f.key]||'—'}</p>)}<p><strong>Additional notes:</strong> {form.notes||'None'}</p><p><strong>Assistance fee:</strong> ₹{service.price_inr}</p></div><div className="cta-row"><button className="btn btn-secondary" onClick={()=>setStep(2)}>Edit application</button><button disabled={busy} onClick={submit}>{busy?'Submitting…':'Confirm & submit request'}</button></div></section>}
  {step===4&&<section className="dashboard-section"><span className="eyebrow">Request submitted</span><h2>We received your request</h2><p className="success-message">{message}</p><div className="request-confirmation"><strong>Request ID</strong><div>{lastOrder?.order_code}</div><p>Status: <strong>{lastOrder?.status||'New'}</strong></p></div><div className="upload-card"><h3>Upload supporting documents</h3><p>Upload documents relevant to this request. Maximum 10 MB per document.</p><form onSubmit={uploadFile}><input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>{const selected=e.target.files?.[0]||null;if(selected&&selected.size>10*1024*1024){setUploadMsg('Please choose a file smaller than 10 MB.');return}setFile(selected)}}/><button type="submit" disabled={!file}>Upload document</button></form>{uploadMsg&&<p className="info" role="status">{uploadMsg}</p>}</div><div className="cta-row"><button onClick={()=>navigate('/my-orders')}>Track my request</button><Link className="btn btn-secondary" to="/">Find another service</Link></div></section>}
 </div>
}
