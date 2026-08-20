import React, {useEffect, useMemo, useState} from 'react'
import {Link, useNavigate, useParams} from 'react-router-dom'
import axios from 'axios'
import {apiBase} from '../services/apiBase'
import {getSession} from '../services/session'
import {getToken, getUser} from '../services/localStorage'

type Step = 1 | 2 | 3 | 4

export default function ServiceDetail(){
 const {id}=useParams(); const navigate=useNavigate()
 const [service,setService]=useState<any>(null); const [loading,setLoading]=useState(true)
 const [step,setStep]=useState<Step>(1); const [form,setForm]=useState({client_name:'',phone:'',email:'',description:''})
 const [file,setFile]=useState<File|null>(null); const [message,setMessage]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false); const [uploadMsg,setUploadMsg]=useState(''); const [lastOrder,setLastOrder]=useState<any>(null)
 const session=getSession(); const user=getUser()

 useEffect(()=>{if(!id)return; axios.get(`${apiBase}/services/${id}`).then(r=>setService(r.data)).catch(()=>setError('Unable to load this service right now.')).finally(()=>setLoading(false))},[id])
 useEffect(()=>{if(session&&!session.is_admin){setForm({client_name:user?.name||'',phone:user?.phone||'',email:user?.email||'',description:''})}},[session?.user_id])

 const serviceQuestions=useMemo(()=>{
   const text=`${service?.name||''} ${service?.keywords||''}`.toLowerCase()
   if(text.includes('scholarship')||text.includes('epass')) return 'Mention your course/class, institution, academic year and whether this is a fresh or renewal application.'
   if(text.includes('poly')||text.includes('eapcet')||text.includes('eamcet')||text.includes('ecet')||text.includes('icet')||text.includes('cet')) return 'Mention your qualification/year, exam name, category (if applicable) and whether you need a fresh application, correction or other assistance.'
   if(text.includes('aadhaar')||text.includes('aadhar')) return 'Tell us the update you need (name, address, date of birth, mobile/document update, etc.). Never send your Aadhaar OTP or password.'
   if(text.includes('pan')) return 'Tell us whether this is a new PAN, correction/update, reprint or other PAN assistance. Never send an OTP or password.'
   if(text.includes('voter')) return 'Tell us whether this is new registration, correction, address/constituency change or another voter-service request.'
   if(text.includes('gurukulam')||text.includes('navodaya')||text.includes('sainik')||text.includes('iiit')||text.includes('admission')) return 'Mention the student class/year, school/college, admission type and any deadline you are working toward.'
   if(text.includes('certificate')) return 'Mention the certificate type, purpose and any deadline or application details that will help us process your request.'
   return 'Describe what you need, any deadline, and any important application details. Do not include passwords, OTPs, PINs or bank details.'
 },[service])

 const submit=async()=>{
   setError(''); setMessage(''); setBusy(true)
   try{
     const r=await axios.post(`${apiBase}/orders`,{...form,service_id:Number(id)},{headers:{Authorization:`Bearer ${getToken()}`}})
     setLastOrder(r.data.order); setMessage(r.data.message); setStep(4)
   }catch(err:any){setError(err?.response?.data?.error||'Unable to submit your request. Please try again.')}finally{setBusy(false)}
 }
 const uploadFile=async(e:React.FormEvent)=>{e.preventDefault(); if(!file||!lastOrder)return; setUploadMsg('Uploading…'); try{const fd=new FormData();fd.append('file',file);fd.append('order_id',String(lastOrder.id));const r=await axios.post(`${apiBase}/uploads`,fd,{headers:{Authorization:`Bearer ${getToken()}`}});setUploadMsg(r.data.message);setFile(null)}catch(err:any){setUploadMsg(err?.response?.data?.error||'Upload failed. Please try again.')}}

 if(loading)return <div className="empty-state">Loading service details…</div>
 if(!service)return <div className="empty-state"><h2>Service unavailable</h2><p>{error||'We could not find this service.'}</p><Link className="btn btn-primary" to="/">Return home</Link></div>
 if(!session||session.is_admin) return <div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p></div><section className="dashboard-section"><h2>Login required</h2><p>Please create or sign in to your client account before requesting this service. Your account lets you securely track the request and documents.</p><Link className="btn btn-primary" to="/login">Login to request</Link><Link className="text-link" to="/register">Create an account →</Link></section></div>

 return <div className="service-detail-page">
   <div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{service.name}</h1><p>{service.description}</p><div className="service-detail-meta"><span>Assistance fee <strong>₹{service.price_inr}</strong></span><span>Official fees, if any, are separate</span></div></div>
   <div className="request-steps" aria-label="Request progress"><span className={step>=1?'active':''}>1. Details</span><span className={step>=2?'active':''}>2. Information</span><span className={step>=3?'active':''}>3. Review</span><span className={step>=4?'active':''}>4. Submitted</span></div>
   {error&&<p className="info" role="alert">{error}</p>}
   {step===1&&<section className="dashboard-section request-form"><span className="eyebrow">Step 1</span><h2>Confirm your contact details</h2><p>These details come from your client account and will be attached to this request.</p><label>Full name<input value={form.client_name} onChange={e=>setForm({...form,client_name:e.target.value})} required/></label><label>Phone<input type="tel" value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} required/></label><label>Email<input type="email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}/></label><button onClick={()=>{if(form.client_name.trim().length<2||form.phone.trim().length<7){setError('Please enter a valid name and phone number.');return}setError('');setStep(2)}}>Continue</button></section>}
   {step===2&&<section className="dashboard-section request-form"><span className="eyebrow">Step 2</span><h2>Tell us what you need</h2><div className="trust-note"><strong>Important:</strong> Never enter OTPs, passwords, PINs or bank details.</div><p>{serviceQuestions}</p><label>Application information / notes<textarea rows={7} minLength={5} value={form.description} onChange={e=>setForm({...form,description:e.target.value})} placeholder="Provide the details needed for your request…" required/></label><div className="cta-row"><button className="btn btn-secondary" onClick={()=>setStep(1)}>Back</button><button onClick={()=>{if(form.description.trim().length<5){setError('Please provide enough information for us to understand your request.');return}setError('');setStep(3)}}>Review request</button></div></section>}
   {step===3&&<section className="dashboard-section"><span className="eyebrow">Step 3</span><h2>Review before submitting</h2><div className="request-summary"><p><strong>Service:</strong> {service.name}</p><p><strong>Name:</strong> {form.client_name}</p><p><strong>Phone:</strong> {form.phone}</p><p><strong>Email:</strong> {form.email||'Not provided'}</p><p><strong>Information:</strong> {form.description}</p><p><strong>Assistance fee:</strong> ₹{service.price_inr}</p></div><div className="cta-row"><button className="btn btn-secondary" onClick={()=>setStep(2)}>Edit</button><button disabled={busy} onClick={submit}>{busy?'Submitting…':'Confirm & submit request'}</button></div></section>}
   {step===4&&<section className="dashboard-section"><span className="eyebrow">Request submitted</span><h2>We received your request</h2><p className="success-message">{message}</p><div className="request-confirmation"><strong>Request ID</strong><div>{lastOrder?.order_code}</div><p>Status: <strong>{lastOrder?.status||'New'}</strong></p></div><div className="upload-card"><h3>Upload supporting documents</h3><p>Upload only documents relevant to this request. Maximum recommended file size is 10 MB per document.</p><form onSubmit={uploadFile}><input type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={e=>{const selected=e.target.files?.[0]||null;if(selected&&selected.size>10*1024*1024){setUploadMsg('Please choose a file smaller than 10 MB.');return}setFile(selected)}}/><button type="submit" disabled={!file}>Upload document</button></form>{uploadMsg&&<p className="info" role="status">{uploadMsg}</p>}</div><div className="cta-row"><button onClick={()=>navigate('/my-orders')}>Track my request</button><Link className="btn btn-secondary" to="/">Find another service</Link></div></section>}
 </div>
}
