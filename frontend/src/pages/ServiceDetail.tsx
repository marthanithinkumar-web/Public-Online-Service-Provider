import React,{useEffect,useMemo,useState} from 'react'
import {Link,useLocation,useNavigate,useParams} from 'react-router-dom'
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
import {fetchJob,formatJobDate,JobNotification} from '../services/jobs'

type Step=1|2|3
type Field={key:string;label:string;placeholder?:string;type?:'text'|'date'|'select';options?:string[];required?:boolean;feeFactor?:boolean}
const SERVICE_TIMEOUT_MS=15000
const apiErrorMessage=(value:any,fallback:string)=>typeof value==='string'?value:Object.values(value||{}).flat().join(' ')||fallback
const JOB_FIELDS:Field[]=[
 {key:'job_post_preference',label:'Post / preference',placeholder:'Post, trade, cadre or preference'},
 {key:'date_of_birth',label:'Date of birth',type:'date'},
 {key:'qualification',label:'Highest / relevant qualification',placeholder:'10th, Intermediate, Degree, Diploma, ITI, etc.'},
 {key:'qualification_board',label:'Board / university',placeholder:'Board or university name'},
 {key:'year_passed',label:'Year passed',placeholder:'Year of passing'},
 {key:'marks_or_cgpa',label:'Marks / percentage / CGPA',placeholder:'As shown on your certificate'},
 {key:'official_registration_number',label:'Existing OTR / registration number',placeholder:'Only if you already have one'},
 {key:'exam_region',label:'Exam centre / region / zone preference',placeholder:'If the recruitment asks for one'},
 {key:'experience',label:'Relevant experience',placeholder:'Employer, role and duration, if applicable'},
 {key:'present_address',label:'Present address',placeholder:'Optional'},
 {key:'permanent_address',label:'Permanent address',placeholder:'Optional'},
]
const JOB_DOCUMENTS=['Recent photograph','Signature image','Date-of-birth / 10th proof','Relevant qualification certificate or marks memo','Identity proof, only if required by the official notice','Category / EWS / PwBD certificate, if applicable','Experience / NOC certificate, if applicable']

function jobSpecificFields(job:JobNotification|null):Field[]{
 const key=(job?.source?.key||'').toLowerCase()
 if(key==='india_post_gds')return [
  {key:'gds_tenth_board',label:'10th board',placeholder:'Board name'},
  {key:'gds_tenth_year',label:'10th passing year',placeholder:'Year'},
  {key:'gds_tenth_result',label:'10th marks / grade',placeholder:'Marks, percentage or grade'},
  {key:'gds_circle_division',label:'Postal circle / division preference',placeholder:'If known'},
  {key:'gds_local_language',label:'Local language studied',placeholder:'Language and class level'},
  {key:'gds_bicycle',label:'Cycling ability',type:'select',options:['Yes','No','Not sure']},
 ]
 if(['ssc','rrb','upsc'].includes(key))return [
  {key:'recruitment_exam_name',label:'Exam / recruitment name',placeholder:job?.title||'Recruitment name'},
  {key:'recruitment_post_order',label:'Post / service preference order',placeholder:'If the notice allows preferences'},
 ]
 return []
}

function feeFactorFields(job:JobNotification|null):Field[]{
 return (job?.fee_factors||[]).map(factor=>({
  key:factor.key,
  label:factor.label,
  type:factor.type==='select'||factor.type==='boolean'?'select':'text',
  options:factor.type==='boolean'?['Yes','No']:(factor.options||[]),
  required:true,
  feeFactor:true,
 }))
}

function ServiceInformation({service,requirements,job}:{service:any,requirements:any,job?:JobNotification|null}){
 const feeFactors=(requirements.fields||[]).filter((field:any)=>field.feeFactor)
 return <section className="service-information" aria-label="Service information">
  {job&&<div className="dashboard-section"><span className="eyebrow">Official job selected</span><h3>{job.title}</h3><p>{job.organization}</p><small>Last date: {formatJobDate(job.deadline)} · Official application fee: {job.application_fee||'As stated in the official notice'}</small>{feeFactors.length>0&&<p><strong>{feeFactors.length} applicant detail{feeFactors.length===1?'':'s'} from the official notification determine your exact official fee.</strong></p>}</div>}
  <div className="service-info-grid"><article><h3>Details</h3><ul>{(requirements.fields||[]).map((field:any)=><li key={field.key}>{field.label} {field.required?'(required to calculate your official fee)':'(optional)'}</li>)}</ul></article><article><h3>Documents</h3>{requirements.documents?.length?<ul>{requirements.documents.map((item:string)=><li key={item}>{item} (optional at request stage)</li>)}</ul>:<p>No document needed now.</p>}</article></div>
  <div className="service-safety-banner"><strong>Never share OTPs, passwords, PINs or banking login details. Complete those steps yourself on the official portal.</strong></div>
 </section>
}

export default function ServiceDetail(){
 const {id,slug}=useParams();const navigate=useNavigate();const location=useLocation();const session=getSession();const user=getUser()
 const [service,setService]=useState<any>(null);const [loading,setLoading]=useState(true);const [step,setStep]=useState<Step>(1)
 const [form,setForm]=useState({client_name:'',phone:'',email:'',notes:''});const [answers,setAnswers]=useState<Record<string,string>>({});const [files,setFiles]=useState<File[]>([]);const [message,setMessage]=useState('');const [error,setError]=useState('');const [busy,setBusy]=useState(false);const [uploadMsg,setUploadMsg]=useState('');const [lastOrder,setLastOrder]=useState<any>(null);const [feeAccepted,setFeeAccepted]=useState(false);const [requestMode,setRequestMode]=useState<'guided'|'express'>('guided');const [job,setJob]=useState<JobNotification|null>(null);const [jobLoading,setJobLoading]=useState(false);const [feeAssessment,setFeeAssessment]=useState<any>(null)
 const jobSlug=new URLSearchParams(location.search).get('job')||''

 useEffect(()=>{let active=true;if(!id&&!slug)return;setLoading(true);setError('');const endpoint=slug?`${apiBase}/services/by-slug/${encodeURIComponent(slug)}`:`${apiBase}/services/${id}`;axios.get(endpoint,{timeout:SERVICE_TIMEOUT_MS}).then(r=>{if(active)setService(r.data)}).catch((e:any)=>{if(active)setError(e?.code==='ECONNABORTED'?'The service server took too long to respond. Please try again.':'Unable to load this service right now.')}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[id,slug])
 useEffect(()=>{if(id&&service?.slug)navigate(`${servicePath(service)}${location.search}`,{replace:true})},[id,service?.slug,navigate,location.search])
 useEffect(()=>{if(!session||session.is_admin)return;const apply=(profile:any)=>setForm(current=>({...current,client_name:profile?.name||current.client_name,phone:profile?.phone||current.phone,email:profile?.email||current.email}));if(user)apply(user);fetchClientProfile().then(result=>apply(result.user)).catch(()=>{if(!user?.name||!user?.phone)setError('Unable to load your contact details. Open Account Settings and confirm your profile.')})},[session?.user_id])
 useEffect(()=>{let active=true;const governmentJobService=service&&(service.catalog_name==='Government Job Application Assistance'||service.name==='Apply Government Job');if(!jobSlug||!governmentJobService){setJob(null);return()=>{active=false}}setJobLoading(true);fetchJob(jobSlug).then(result=>{if(active)setJob(result.job)}).catch(()=>{if(active)setError('The selected official job notice is unavailable or has closed. Please choose a current job notice.')}).finally(()=>{if(active)setJobLoading(false)});return()=>{active=false}},[jobSlug,service?.id])

 const baseRequirements=service?.requirements||{fields:[],documents:[],safety_note:'Never provide OTPs, passwords, PINs, CVV, banking credentials, or account recovery codes.'}
 const requirements=useMemo(()=>job?{
   ...baseRequirements,
   fields:[...feeFactorFields(job),...(baseRequirements.fields||[]).map((field:any)=>({...field,required:false})),...JOB_FIELDS,...jobSpecificFields(job)].filter((field:any,index:number,all:any[])=>all.findIndex(item=>item.key===field.key)===index),
   documents:[...(baseRequirements.documents||[]),...JOB_DOCUMENTS].filter((item:string,index:number,all:string[])=>all.indexOf(item)===index),
 }:baseRequirements,[service?.id,job?.id,job?.fee_rules_verified])
 const fields=useMemo<Field[]>(()=>requirements.fields||[],[requirements])
 const requiredFeeFields=useMemo(()=>fields.filter(field=>field.required&&field.feeFactor),[fields])
 const updateAnswer=(key:string,value:string)=>{setAnswers(a=>({...a,[key]:value}));setFeeAssessment(null)}
 const addFiles=(selected:File[])=>{const oversized=selected.find(item=>item.size>10*1024*1024);if(oversized){setError(`${oversized.name} is larger than 10 MB.`);return}setFiles(current=>{const existing=new Set(current.map(item=>`${item.name}:${item.size}:${item.lastModified}`));const additions=selected.filter(item=>!existing.has(`${item.name}:${item.size}:${item.lastModified}`));if(current.length+additions.length>20){setError(`You can upload a maximum of 20 documents for one request. You already selected ${current.length}.`);return current}setError('');return [...current,...additions]})}
 const reviewRequest=async()=>{if(form.client_name.trim().length<2||form.phone.trim().length<7){setError('Please complete your name and phone number in Account Settings.');return}const missing=requiredFeeFields.filter(field=>!String(answers[field.key]||'').trim());if(missing.length){setError(`Complete the official fee details: ${missing.map(field=>field.label).join(', ')}.`);return}setRequestMode('guided');setError('');if(job&&job.fee_rules_verified&&requiredFeeFields.length){try{const response=await axios.post(`${apiBase}/fees/jobs/${encodeURIComponent(job.slug)}/assess`,{answers},{headers:{Authorization:`Bearer ${getToken()}`},timeout:SERVICE_TIMEOUT_MS});setFeeAssessment(response.data)}catch(e:any){setError(e?.response?.data?.error||'Unable to calculate the official fee from the verified notification rules.');return}}else if(job){setFeeAssessment({status:'unconfirmed'})}setStep(2)}
 const submit=async()=>{setError('');setMessage('');setUploadMsg('');setBusy(true);try{const application_data:any={...(requestMode==='guided'?answers:{}),request_notes:requestMode==='guided'?form.notes.trim():'',service_name:service.name,request_mode:requestMode};if(job){Object.assign(application_data,{job_id:job.id,job_slug:job.slug,job_title:job.title,job_organization:job.organization,job_deadline:job.deadline,job_official_notice_url:job.official_notice_url,job_application_url:job.application_url,job_source:job.source?.name||null,job_official_fee_notice_text:job.application_fee||null})}const r=await axios.post(`${apiBase}/orders/`,{service_id:Number(service.id),application_data},{headers:{Authorization:`Bearer ${getToken()}`},timeout:SERVICE_TIMEOUT_MS});const order=r.data.order;setLastOrder(order);let uploaded=0;for(const selected of files){try{const fd=new FormData();fd.append('file',selected);fd.append('order_id',String(order.id));await axios.post(`${apiBase}/uploads/`,fd,{headers:{Authorization:`Bearer ${getToken()}`},timeout:30000});uploaded+=1}catch{setUploadMsg(`${uploaded} of ${files.length} documents uploaded. You can contact the admin if a document needs to be resent.`);break}}if(files.length&&uploaded===files.length)setUploadMsg(`${uploaded} document${uploaded===1?'':'s'} uploaded securely.`);setMessage(r.data.message);setStep(3)}catch(err:any){setError(err?.code==='ECONNABORTED'?'Submission timed out. Please try again.':apiErrorMessage(err?.response?.data?.error,'Unable to submit your request. Please try again.'))}finally{setBusy(false)}}
 const canonicalPath=service?servicePath(service):`/services/${slug||''}`
 const returnTo=encodeURIComponent(`${canonicalPath}${location.search}`)

 if(loading||jobLoading)return <div className="empty-state">Loading application details…</div>
 if(!service)return <><Seo title="Service unavailable" description="The requested public-service assistance page is unavailable." path={canonicalPath} index={false}/><div className="empty-state"><h2>Service unavailable</h2><p>{error||'We could not find this service.'}</p><button className="btn btn-secondary" onClick={()=>window.location.reload()}>Try again</button><Link className="btn btn-primary" to="/">Return home</Link></div></>
 const seoDescription=`${service.description} Review assistance requirements, fees, documents and the request process.`
 const serviceSchema=[{'@context':'https://schema.org','@type':'BreadcrumbList',itemListElement:[{'@type':'ListItem',position:1,name:'Home',item:SITE.url},{'@type':'ListItem',position:2,name:service.category||'Services',item:`${SITE.url}/#services`},{'@type':'ListItem',position:3,name:service.name,item:`${SITE.url}${canonicalPath}`}]},{'@context':'https://schema.org','@type':'Service',name:service.name,description:service.description,serviceType:service.category||'Public-service application assistance',provider:{'@type':'Organization',name:SITE.name,url:SITE.url},areaServed:{'@type':'Country',name:'India'},url:`${SITE.url}${canonicalPath}`},]
 const seo=<Seo title={job?`Apply ${job.title}`:service.name} description={job?`Request application assistance for ${job.title} from ${job.organization}.`:seoDescription} path={canonicalPath} type="article" schema={serviceSchema}/>
 if(!session)return <>{seo}<div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{job?`Apply ${job.title}`:service.name}</h1><p>{job?`${job.organization} · Last date ${formatJobDate(job.deadline)}`:service.description}</p><FeeSummary data={service}/>{job&&<p className="info">Official application fee: <strong>{job.application_fee||'As applicable under the official notice'}</strong>. Your exact official fee is calculated from the applicant conditions stated in this notification when verified rules are available.</p>}</div><ServiceInformation service={service} requirements={requirements} job={job}/><section className="dashboard-section service-request-cta"><h2>Ready to request this application?</h2><p>Sign in or create an account. After authentication, you will return directly here and continue the guided request.</p><div className="cta-row"><Link className="btn btn-primary" to={`/login?returnTo=${returnTo}`}>Sign in & continue</Link><Link className="btn btn-secondary" to={`/register?returnTo=${returnTo}`}>Create account</Link></div></section></div></>
 if(session.is_admin)return <>{seo}<div className="service-detail-page"><div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{job?`Apply ${job.title}`:service.name}</h1><p>{job?job.organization:service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Client requests only</h2><p>Admin accounts manage incoming requests from the admin dashboard. Please use a client account to submit a service request.</p><Link className="btn btn-primary" to="/admin/dashboard">Go to admin dashboard</Link></section></div></>

 return <>{seo}<div className="service-detail-page">
 <div className="service-detail-hero"><span className="eyebrow">{service.category||'Public service'}</span><h1>{job?`Apply ${job.title}`:service.name}</h1><p>{job?`${job.organization} · Last date ${formatJobDate(job.deadline)}`:service.description}</p><FeeSummary data={service}/>{job&&<p className="info">Official application fee: <strong>{job.application_fee||'As applicable under the official notice'}</strong>. Your exact fee can vary by the applicant conditions in this notification.</p>}</div>
  <div className="request-steps simplified" aria-label="Request progress"><span className={step>=1?'active':''} aria-current={step===1?'step':undefined}>1. Details</span><span className={step>=2?'active':''} aria-current={step===2?'step':undefined}>2. Review</span><span className={step>=3?'active':''} aria-current={step===3?'step':undefined}>3. Submitted</span></div>
  {error&&<p className="info" role="alert">{error}</p>}
  {step===1&&<section className="dashboard-section request-form simplified-request-form">
    <span className="eyebrow">Step 1</span><h2>{job?'Job application details':'Request details'}</h2>
    <div className="request-contact-summary"><div><strong>{form.client_name||'Profile name required'}</strong><span>{form.phone||'Phone required'}{form.email?` · ${form.email}`:''}</span></div><Link to="/account-settings">Edit profile</Link></div>
    {job&&<div className="request-summary"><p><strong>Job:</strong> {job.title}</p><p><strong>Organization:</strong> {job.organization}</p><p><strong>Last date:</strong> {formatJobDate(job.deadline)}</p><p><a href={job.official_notice_url} target="_blank" rel="noopener noreferrer">Read official notification ↗</a></p></div>}
    {requiredFeeFields.length>0&&<div className="dashboard-section"><h3>Required to calculate your official fee</h3><p className="request-short-hint">These questions come from the fee conditions verified for this specific official notification. They can differ for every recruitment.</p>{requiredFeeFields.map(field=><label key={field.key}>{field.label} *{field.type==='select'?<select required value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}><option value="">Select</option>{(field.options||[]).map(option=><option key={option} value={option}>{option}</option>)}</select>:<input required type={field.type||'text'} placeholder={field.placeholder} value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}/>}</label>)}</div>}
    {job&&!job.fee_rules_verified&&<p className="info">The exact person-specific fee rules for this notification have not yet been verified in the system. Your request can still be submitted, but payment will stay blocked until the admin confirms your correct official fee from the official notification.</p>}
    {fields.filter(field=>!field.feeFactor).length>0&&<><h3>{job?'Other useful job details (optional)':'Service details (optional)'}</h3><p className="request-short-hint">Add any details you know to help the admin process your request faster.</p>{fields.filter(field=>!field.feeFactor).map(field=><label key={field.key}>{field.label}{field.type==='select'?<select value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}><option value="">Select</option>{(field.options||[]).map(option=><option key={option} value={option}>{option}</option>)}</select>:<input type={field.type||'text'} placeholder={field.placeholder} value={answers[field.key]||''} onChange={event=>updateAnswer(field.key,event.target.value)}/>}</label>)}</>}
    <label>Notes<textarea rows={3} value={form.notes} onChange={event=>setForm({...form,notes:event.target.value})} placeholder="Short note, if needed"/></label>
    {requirements.documents?.length>0&&<div className="upload-card"><h3>{job?'Documents relevant to this job (optional)':'Documents for this service'}</h3><ul>{requirements.documents.map((item:string)=><li key={item}>{item}</li>)}</ul>{job&&<p className="request-short-hint">Upload only documents that apply to you. All uploads are optional when submitting the assistance request; the admin can ask for anything still needed.</p>}<label>Upload documents (multiple)<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={event=>{addFiles(Array.from(event.target.files||[]));event.target.value='' }}/></label><small>Add files once or in several selections · PDF, PNG or JPG · maximum 20 files · maximum 10 MB each</small>{files.length>0&&<><p className="selected-file-count" role="status">{files.length} document{files.length===1?'':'s'} selected</p><ul className="document-list selected-documents">{files.map((item,index)=><li key={`${item.name}-${item.size}-${item.lastModified}`}><span>{item.name}</span><button className="btn-secondary" type="button" onClick={()=>setFiles(current=>current.filter((_,itemIndex)=>itemIndex!==index))}>Remove</button></li>)}</ul></>}</div>}
    <p className="request-safety-line">Do not enter OTPs, passwords, PINs or banking details. You will authorize those steps yourself on the official portal.</p>
    <div className="cta-row"><button type="button" onClick={reviewRequest}>Review request</button></div>
  </section>}
  {step===2&&<section className="dashboard-section simplified-review"><span className="eyebrow">Step 2</span><h2>Review and submit</h2><div className="request-summary"><p><strong>{job?'Job':'Service'}:</strong> {job?`${job.title} — ${job.organization}`:service.name}</p><p><strong>Client:</strong> {form.client_name} · {form.phone}</p>{requestMode==='guided'&&fields.filter(f=>answers[f.key]).map(f=><p key={f.key}><strong>{f.label}:</strong> {answers[f.key]}</p>)}{form.notes&&<p><strong>Notes:</strong> {form.notes}</p>}</div><FeeSummary data={service} compact/>{job&&feeAssessment?.status==='known'&&<p className="success-message"><strong>Your official application fee from the verified notification rules:</strong> ₹{Number(feeAssessment.amount_inr||0).toFixed(2)}{feeAssessment.matched_rule?` — ${feeAssessment.matched_rule}`:''}</p>}{job&&feeAssessment?.status!=='known'&&<p className="info"><strong>Official application fee:</strong> will be confirmed from the official notification before payment. Razorpay remains unavailable until the exact amount for you is known.</p>}<label className="fee-acknowledgement"><input type="checkbox" checked={feeAccepted} onChange={e=>setFeeAccepted(e.target.checked)}/> I agree to the assistance fee shown above and the person-specific official fee calculated/confirmed for this application.</label><div className="cta-row"><button type="button" className="btn btn-secondary" onClick={()=>setStep(1)}>Edit</button><button type="button" disabled={busy||!feeAccepted} onClick={submit}>{busy?'Submitting…':'Submit request'}</button></div></section>}
  {step===3&&<section className="dashboard-section simplified-confirmation"><span className="eyebrow">Submitted</span><h2>We are reviewing your request</h2>{!job&&<p>Expected completion: 5 days to 1 week.</p>}{job&&<p>We will process this request against the selected official job notice and its deadline. You must personally complete any OTP, account login or payment authorization required by the official portal.</p>}<p className="success-message">{message}</p><div className="request-confirmation"><strong>Order number</strong><div>{lastOrder?.order_code}</div><p>Status: <strong>{lastOrder?.status||'Submitted'}</strong></p></div>{uploadMsg&&<p className="info" role="status">{uploadMsg}</p>}<div className="request-summary"><p><strong>Admin:</strong> {PROVIDER.name}</p><p><strong>Contact:</strong> <a href={`tel:${PROVIDER.phone}`}>{PROVIDER.phone}</a> · <a href={`mailto:${PROVIDER.email}`}>{PROVIDER.email}</a></p></div>{lastOrder?.id&&<RequestFeedback fixedOrderId={lastOrder.id}/>}<div className="cta-row">{lastOrder?.id&&<Link className="btn btn-primary" to={`/my-orders/${lastOrder.id}`}>Open request & payment</Link>}<Link className="btn btn-secondary" to="/messages">Chat with Admin</Link></div></section>}
 </div></>
}
