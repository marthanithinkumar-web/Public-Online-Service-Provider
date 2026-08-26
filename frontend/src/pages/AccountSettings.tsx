import React, {useEffect,useState} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import axios from 'axios'
import {deleteAccount,fetchClientProfile,updateClientProfile} from '../services/auth'

export default function AccountSettings(){
  const navigate=useNavigate()
  const initialSection=window.location.hash==='#delete-account'?'delete':'profile'
  const [section,setSection]=useState<'profile'|'applications'|'support'|'privacy'|'delete'>(initialSection)
  const [profile,setProfile]=useState({name:'',email:'',phone:''})
  const [currentPassword,setCurrentPassword]=useState('')
  const [newPassword,setNewPassword]=useState('')
  const [deletePassword,setDeletePassword]=useState('')
  const [deleteConfirm,setDeleteConfirm]=useState('')
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')
  const [activeRequests,setActiveRequests]=useState<any[]>([])

  useEffect(()=>{fetchClientProfile().then(result=>setProfile(result.user)).catch(()=>setError('Unable to load your profile.'))},[])
  const save=async(event:React.FormEvent)=>{event.preventDefault();setMessage('');setError('');try{setBusy(true);const result=await updateClientProfile({...profile,current_password:currentPassword,new_password:newPassword});setProfile(result.user);setCurrentPassword('');setNewPassword('');setMessage(result.message)}catch(err){setError(axios.isAxiosError(err)?err.response?.data?.error||'Unable to update your profile.':'Unable to update your profile.')}finally{setBusy(false)}}
  const remove=async(event:React.FormEvent)=>{event.preventDefault();setMessage('');setError('');setActiveRequests([]);if(!deletePassword){setError('Enter your current password to continue.');return}if(deletePassword!==deleteConfirm){setError('The passwords do not match.');return}if(!window.confirm('This permanently deletes your account and closed client-owned data. This action cannot be undone. Continue?'))return;try{setBusy(true);await deleteAccount(deletePassword);setMessage('Your account has been permanently deleted. Redirecting…');setTimeout(()=>navigate('/'),1200)}catch(err){if(axios.isAxiosError(err)){setError(err.response?.data?.error||'Unable to delete the account.');setActiveRequests(err.response?.data?.active_requests||[])}else setError('Unable to delete the account.')}finally{setBusy(false)}}

  const choose=(next:typeof section)=>{setSection(next);setError('');setMessage('');window.history.replaceState(null,'',next==='delete'?'#delete-account':'#'+next)}

  return <div className="settings-page">
    <section className="dashboard-hero settings-hero"><div><span className="eyebrow">Your account</span><h1>Profile & security</h1><p>Keep your contact details current and protect access to your applications.</p></div><Link className="btn btn-secondary" to="/my-orders">Back to dashboard</Link></section>
    {error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}
    <div className="account-shell">
      <aside className="account-sidebar"><div className="account-sidebar-title"><strong>Account menu</strong><small>Profile and account management</small></div><nav aria-label="Client account navigation">
        <button className={section==='profile'?'active':''} onClick={()=>choose('profile')} type="button"><span>Profile & security</span><small>Contact details and password</small></button>
        <button className={section==='applications'?'active':''} onClick={()=>choose('applications')} type="button"><span>My applications</span><small>Requests and history</small></button>
        <button className={section==='support'?'active':''} onClick={()=>choose('support')} type="button"><span>Help & feedback</span><small>Grievances and reviews</small></button>
        <button className={section==='privacy'?'active':''} onClick={()=>choose('privacy')} type="button"><span>Privacy & account</span><small>How your account is managed</small></button>
        <button className={`account-delete-link ${section==='delete'?'active':''}`} onClick={()=>choose('delete')} type="button"><span>Delete account</span><small>Protected permanent action</small></button>
      </nav></aside>
      <div className="account-content">
      {section==='profile'&&<form className="dashboard-section auth-form" onSubmit={save}><span className="eyebrow">Client profile</span><h2>Personal details</h2><label>Name<input required value={profile.name||''} onChange={event=>setProfile({...profile,name:event.target.value})}/></label><label>Email<input required type="email" value={profile.email||''} onChange={event=>setProfile({...profile,email:event.target.value})}/></label><label>Phone<input required type="tel" value={profile.phone||''} onChange={event=>setProfile({...profile,phone:event.target.value})}/></label><h3>Change password</h3><p className="auth-hint">Current password is required when changing your email or password.</p><label>Current password<input type="password" autoComplete="current-password" value={currentPassword} onChange={event=>setCurrentPassword(event.target.value)}/></label><label>New password<input type="password" minLength={8} autoComplete="new-password" value={newPassword} onChange={event=>setNewPassword(event.target.value)} placeholder="Leave blank to keep current password"/></label><button disabled={busy}>{busy?'Saving…':'Save profile and security'}</button></form>}
      {section==='applications'&&<section className="dashboard-section settings-card"><span className="eyebrow">Applications</span><h2>Your service requests</h2><p>Open your dashboard to review active requests, status timelines, documents and completed application history.</p><Link className="btn btn-primary" to="/my-orders#applications">Open my applications</Link></section>}
      {section==='support'&&<section className="dashboard-section settings-card"><span className="eyebrow">Help & feedback</span><h2>How can we help?</h2><p>Raise a private grievance about a request or share a review after receiving assistance.</p><div className="settings-links"><Link to="/submit-grievance">Submit a grievance <span>→</span></Link><Link to="/submit-review">Share a review <span>→</span></Link></div></section>}
      {section==='privacy'&&<section className="dashboard-section settings-card"><span className="eyebrow">Privacy</span><h2>Account management</h2><p>Your requests and documents are protected by account ownership checks. Only you and authorized provider administrators can access the information required to process your requests.</p><p>Account deletion is available separately below the account-management area and always requires password verification.</p></section>}
      {section==='delete'&&<form onSubmit={remove} className="dashboard-section auth-form danger-card"><span className="eyebrow">Protected action</span><h2>Delete account</h2><div className="deletion-warning" role="note"><strong>Review this before continuing</strong><p>This permanently removes your client account, closed applications, grievances, reviews, notifications and uploaded documents.</p><p>For your protection, an account with an active request cannot be deleted. Cancel an eligible request from its application page, or contact the provider if processing has already started.</p><p>This action cannot be undone and all active sessions will stop working.</p></div>{activeRequests.length>0&&<div className="active-request-warning"><strong>Resolve these active requests first</strong>{activeRequests.map(request=><Link key={request.id} to={`/my-orders/${request.id}`}>{request.order_code} · {request.status}</Link>)}</div>}<p className="auth-hint">To prevent accidental deletion, enter your current password twice. A final confirmation will appear before anything is removed.</p><label>Current password<input type="password" autoComplete="current-password" value={deletePassword} onChange={event=>setDeletePassword(event.target.value)} disabled={busy}/></label><label>Confirm current password<input type="password" autoComplete="current-password" value={deleteConfirm} onChange={event=>setDeleteConfirm(event.target.value)} disabled={busy}/></label><button className="danger-button" disabled={busy||!deletePassword||!deleteConfirm}>{busy?'Deleting account…':'Continue to final confirmation'}</button></form>}
      </div>
    </div>
  </div>
}
