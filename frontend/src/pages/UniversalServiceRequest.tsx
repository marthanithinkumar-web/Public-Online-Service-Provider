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
 {key:'qualification_board',label:'Board / university'},
 {key:'year_passed',label:'Year passed'},
 {key:'marks_or_cgpa',label:'Marks / percentage / CGPA'},
 {key:'official_registration_number',label:'Existing OTR / registration number'},
 {key:'exam_region',label:'Exam centre / region / zone preference'},
 {key:'experience',label:'Relevant experience'},
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
const COMMON_CERTIFICATE_FIELDS:Field[]=[
 {key:'applicant_name',label:'Applicant name'},
 {key:'date_of_birth',label:'Date of birth',type:'date'},
 {key:'father_or_guardian_name',label:'Father / mother / guardian name'},
 {key:'address',label:'Current address'},
 {key:'district',label:'District'},
 {key:'mandal_or_tehsil',label:'Mandal / Tahsil'},
]
const SERVICE_FIELD_PROFILES:Array<{match:RegExp;fields:Field[]}>= [
 {match:/income certificate|income.*certificate/i,fields:[...COMMON_CERTIFICATE_FIELDS,{key:'occupation',label:'Occupation'},{key:'family_income',label:'Annual family income'},{key:'income_source',label:'Main source of income'},{key:'purpose',label:'Purpose for certificate'}]},
 {match:/caste|community|bc certificate|sc certificate|st certificate|ews certificate/i,fields:[...COMMON_CERTIFICATE_FIELDS,{key:'community',label:'Community / caste'},{key:'sub_caste',label:'Sub-caste / group'},{key:'religion',label:'Religion'},{key:'existing_family_certificate',label:'Existing family caste / community certificate number'},{key:'purpose',label:'Purpose for certificate'}]},
 {match:/residence|domicile|nativity/i,fields:[...COMMON_CERTIFICATE_FIELDS,{key:'years_at_address',label:'Years living at current address'},{key:'previous_address',label:'Previous address'},{key:'purpose',label:'Purpose for certificate'}]},
 {match:/birth certificate/i,fields:[{key:'child_name',label:'Name on birth record'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'place_of_birth',label:'Place of birth'},{key:'father_name',label:"Father's name"},{key:'mother_name',label:"Mother's name"},{key:'hospital_or_registration',label:'Hospital / registration details'},{key:'registration_number',label:'Birth registration number'}]},
 {match:/death certificate/i,fields:[{key:'deceased_name',label:'Name of deceased'},{key:'date_of_death',label:'Date of death',type:'date'},{key:'place_of_death',label:'Place of death'},{key:'relative_name',label:'Father / spouse / relative name'},{key:'applicant_relation',label:'Your relation to the deceased'},{key:'hospital_or_registration',label:'Hospital / registration details'},{key:'registration_number',label:'Death registration number'}]},
 {match:/marriage certificate/i,fields:[{key:'bride_name',label:'Bride name'},{key:'groom_name',label:'Groom name'},{key:'marriage_date',label:'Date of marriage',type:'date'},{key:'marriage_place',label:'Place of marriage'},{key:'bride_dob',label:'Bride date of birth',type:'date'},{key:'groom_dob',label:'Groom date of birth',type:'date'},{key:'registration_number',label:'Existing marriage registration number'}]},
 {match:/ration|food security|rice card/i,fields:[{key:'head_of_family',label:'Head of family'},{key:'ration_card_number',label:'Existing ration / food security card number'},{key:'family_members',label:'Family member details'},{key:'address',label:'Current address'},{key:'district',label:'District'},{key:'annual_income',label:'Annual family income'}]},
 {match:/voter|electoral/i,fields:[{key:'applicant_name',label:'Applicant name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'epic_number',label:'Existing EPIC / Voter ID number'},{key:'address',label:'Current address'},{key:'assembly_constituency',label:'Assembly constituency'},{key:'request_type',label:'Registration / correction / address change details'}]},
 {match:/aadhaar/i,fields:[{key:'aadhaar_last_four',label:'Last 4 digits of Aadhaar'},{key:'request_type',label:'Update / correction requested'},{key:'current_name',label:'Current name on Aadhaar'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'address',label:'Address details'},{key:'registered_mobile',label:'Registered mobile number'}]},
 {match:/pan card|pan application|permanent account/i,fields:[{key:'applicant_name',label:'Applicant name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'father_name',label:"Father's name"},{key:'pan_number',label:'Existing PAN number'},{key:'aadhaar_last_four',label:'Last 4 digits of Aadhaar'},{key:'request_type',label:'New PAN / correction / reprint'},{key:'address',label:'Communication address'}]},
 {match:/passport/i,fields:[{key:'applicant_name',label:'Applicant name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'place_of_birth',label:'Place of birth'},{key:'father_name',label:"Father's name"},{key:'mother_name',label:"Mother's name"},{key:'passport_number',label:'Existing passport number'},{key:'request_type',label:'Fresh / reissue / correction'},{key:'address',label:'Current address'}]},
 {match:/driving licence|driver.*licen|learner.*licen/i,fields:[{key:'applicant_name',label:'Applicant name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'licence_number',label:'Existing licence number'},{key:'vehicle_class',label:'Vehicle class'},{key:'request_type',label:'Learner / new / renewal / correction'},{key:'rto',label:'RTO / transport office'},{key:'address',label:'Current address'}]},
 {match:/land|pahani|adangal|1b|mutation|property/i,fields:[{key:'owner_name',label:'Owner / pattadar name'},{key:'survey_number',label:'Survey / sub-division number'},{key:'village',label:'Village'},{key:'mandal',label:'Mandal'},{key:'district',label:'District'},{key:'extent',label:'Land extent'},{key:'document_number',label:'Existing document / passbook number'},{key:'request_type',label:'Record / mutation / certificate request'}]},
 {match:/pension/i,fields:[{key:'beneficiary_name',label:'Beneficiary name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'pension_type',label:'Pension type'},{key:'pension_id',label:'Existing pension / beneficiary ID'},{key:'bank_last_four',label:'Last 4 digits of bank account'},{key:'address',label:'Current address'}]},
 {match:/scheme|welfare|benefit/i,fields:[{key:'beneficiary_name',label:'Beneficiary name'},{key:'date_of_birth',label:'Date of birth',type:'date'},{key:'category',label:'Category / community'},{key:'annual_income',label:'Annual family income'},{key:'occupation',label:'Occupation'},{key:'address',label:'Current address'},{key:'beneficiary_id',label:'Existing beneficiary / scheme ID'}]},
]

function cachedService(id?:string,slug?:string){
 const normalized=slug?slugifyServiceName(slug):''
 return readCachedServices(true).find((item:any)=>id?String(item.id)===String(id):normalized&&[item.slug,slugifyServiceName(item.name),slugifyServiceName(item.catalog_name||'')].filter(Boolean).includes(normalized))||null
}
function inferredServiceFields(service:any):Field[]{
 const text=[service?.name,service?.catalog_name,service?.category,service?.description].filter(Boolean).join(' ')
 const profile=SERVICE_FIELD_PROFILES.find(item=>item.match.test(text))
 return profile?.fields||[]
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
  const serviceFields:Field[]=(requirements.fields||[]).map((field:any)=>({key:String(field.key),label:String(field.label||field.key),type:field.type==='date'||field.type==='select'?field.type:'text',options:Array.isArray(field.options)?field.options:undefined,placeholder:field.placeholder,feeFactor:Boolean(field.feeFactor)}))
  const specificFields=inferredServiceFields(service)
  const jobFeeFields:Field[]=(job?.fee_factors||[]).map((factor:any)=>({key:String(factor.key),label:String(factor.label),type:factor.type==='select'||factor.type==='boolean'?'select':'text',options:factor.type==='boolean'?['Yes','No']:(factor.options||[]),feeFactor:true}))
  const base:Field[]=specificFields.length?[...specificFields,...serviceFields]:serviceFields.length?serviceFields:FALLBACK_FIELDS
  const source:Field[]=scholarship?[...SCHOLARSHIP_FIELDS,...base]:job?[...jobFeeFields,...JOB_FIELDS,...base]:base
  return source.filter((field,index,all)=>all.findIndex(other=>other.key===field.key)===index)
 },[service?.id,service?.name,service?.catalog_name,service?.category,job?.id,scholarship?.id])
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
 if(!session)return <div className="service-detail-page"><Seo title={title} description={service.description||'Application assistance request'} path={location.pathname}/><div className="service-detail-hero"><h1>{title}</h1><p>{service.description}</p><FeeSummary data={service}/></div><section className="dashboard-section"><h2>Enter details before payment</h2><p>Sign in first. You will return here to enter the application details you know, submit the request, and then continue to fee payment.</p><div className="cta-row"><Link className="btn btn-primary" to={`/login?returnTo=${returnTo}`}>Client login</Link><Link className="btn btn-secondary" to={`/register?returnTo=${returnTo}`}>Create account</Link></div></section></div>
 if(session.is_admin)return <div className="empty-dashboard"><h1>Client request page</h1><p>Use a client account to submit service applications.</p><Link to="/admin/dashboard">Admin dashboard</Link></div>
 return <div className="service-detail-page"><Seo title={title} description={service.description||'Application assistance request'} path={location.pathname}/><div className="service-detail-hero"><span className="eyebrow">Application details</span><h1>{title}</h1><p>{service.description}</p><FeeSummary data={service}/>{scholarship&&<p className="info">Scholarships have no official application fee in this assistance flow. Only the website assistance fee applies.</p>}</div><section className="dashboard-section request-form simplified-request-form"><h2>Enter application details</h2><p className="request-short-hint">Enter the details you know for this {job?'job':scholarship?'scholarship':'service'} and leave anything you do not know blank.</p><div className="request-contact-summary"><div><strong>{profile?.name}</strong><span>{profile?.phone}{profile?.email?` · ${profile.email}`:''}</span></div><Link to="/account-settings">Edit profile</Link></div>{fields.map(field=><label key={field.key}>{field.label}{field.type==='select'?<select value={answers[field.key]||''} onChange={e=>setAnswers(current=>({...current,[field.key]:e.target.value}))}><option value="">Select</option>{(field.options||[]).map(option=><option key={option} value={option}>{option}</option>)}</select>:<input type={field.type||'text'} value={answers[field.key]||''} placeholder={field.placeholder||''} onChange={e=>setAnswers(current=>({...current,[field.key]:e.target.value}))}/>}</label>)}<label>Additional details<textarea rows={4} value={notes} onChange={e=>setNotes(e.target.value)} placeholder="Add anything that will help us process the application"/></label>{(requirements.documents||[]).length>0&&<div className="upload-card"><h3>Documents</h3><ul>{(requirements.documents||[]).map((item:string)=><li key={item}>{item}</li>)}</ul><label>Upload documents<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg" onChange={e=>setFiles(Array.from(e.target.files||[]).slice(0,20))}/></label>{files.length>0&&<p>{files.length} file{files.length===1?'':'s'} selected</p>}</div>}<p className="request-safety-line">Do not enter OTPs, passwords, PINs or banking login details. Complete those steps yourself only on the official portal.</p>{error&&<p className="info" role="alert">{error}</p>}<button className="btn btn-primary" type="button" disabled={busy} onClick={submit}>{busy?'Submitting…':'Submit application'}</button><p className="request-short-hint">After submission, you will continue to the request page for fee payment and tracking.</p></section></div>
}
