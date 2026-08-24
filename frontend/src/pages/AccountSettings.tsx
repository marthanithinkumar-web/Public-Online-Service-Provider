import React, {useEffect,useState} from 'react'
import {Link,useNavigate} from 'react-router-dom'
import axios from 'axios'
import {deleteAccount,fetchClientProfile,updateClientProfile} from '../services/auth'

export default function AccountSettings(){
  const navigate=useNavigate()
  const [profile,setProfile]=useState({name:'',email:'',phone:''})
  const [currentPassword,setCurrentPassword]=useState('')
  const [newPassword,setNewPassword]=useState('')
  const [deletePassword,setDeletePassword]=useState('')
  const [deleteConfirm,setDeleteConfirm]=useState('')
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')

  useEffect(()=>{fetchClientProfile().then(result=>setProfile(result.user)).catch(()=>setError('Unable to load your profile.'))},[])
  const save=async(event:React.FormEvent)=>{event.preventDefault();setMessage('');setError('');try{setBusy(true);const result=await updateClientProfile({...profile,current_password:currentPassword,new_password:newPassword});setProfile(result.user);setCurrentPassword('');setNewPassword('');setMessage(result.message)}catch(err){setError(axios.isAxiosError(err)?err.response?.data?.error||'Unable to update your profile.':'Unable to update your profile.')}finally{setBusy(false)}}
  const remove=async(event:React.FormEvent)=>{event.preventDefault();setMessage('');setError('');if(!deletePassword){setError('Enter your current password to continue.');return}if(deletePassword!==deleteConfirm){setError('The passwords do not match.');return}if(!window.confirm('This permanently deletes your account and client-owned data. This action cannot be undone. Continue?'))return;try{setBusy(true);await deleteAccount(deletePassword);setMessage('Your account has been permanently deleted. Redirecting…');setTimeout(()=>navigate('/'),1200)}catch(err){setError(axios.isAxiosError(err)?err.response?.data?.error||'Unable to delete the account.':'Unable to delete the account.')}finally{setBusy(false)}}

  return <div className="settings-page">
    <section className="dashboard-hero settings-hero"><div><span className="eyebrow">Your account</span><h1>Profile & security</h1><p>Keep your contact details current and protect access to your applications.</p></div><Link className="btn btn-secondary" to="/my-orders">Back to dashboard</Link></section>
    {error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}
    <div className="settings-grid">
      <form className="dashboard-section auth-form" onSubmit={save}><span className="eyebrow">Client profile</span><h2>Personal details</h2><label>Name<input required value={profile.name||''} onChange={event=>setProfile({...profile,name:event.target.value})}/></label><label>Email<input required type="email" value={profile.email||''} onChange={event=>setProfile({...profile,email:event.target.value})}/></label><label>Phone<input required type="tel" value={profile.phone||''} onChange={event=>setProfile({...profile,phone:event.target.value})}/></label><h3>Change password</h3><p className="auth-hint">Current password is required when changing your email or password.</p><label>Current password<input type="password" autoComplete="current-password" value={currentPassword} onChange={event=>setCurrentPassword(event.target.value)}/></label><label>New password<input type="password" minLength={8} autoComplete="new-password" value={newPassword} onChange={event=>setNewPassword(event.target.value)} placeholder="Leave blank to keep current password"/></label><button disabled={busy}>{busy?'Saving…':'Save profile and security'}</button></form>
      <section className="dashboard-section settings-card"><span className="eyebrow">Account</span><h2>Application shortcuts</h2><p>Review your applications, get help, or share feedback.</p><div className="settings-links"><Link to="/my-orders#applications">My applications <span>→</span></Link><Link to="/submit-grievance">Get help <span>→</span></Link><Link to="/submit-review">Share a review <span>→</span></Link></div></section>
      <form onSubmit={remove} className="dashboard-section auth-form danger-card"><span className="eyebrow">Privacy</span><h2>Delete account</h2><p>Permanently removes your client account, applications, grievances, reviews, notifications and uploaded documents.</p><p className="auth-hint">Your current password is required. This cannot be undone.</p><label>Current password<input type="password" autoComplete="current-password" value={deletePassword} onChange={event=>setDeletePassword(event.target.value)} disabled={busy}/></label><label>Confirm current password<input type="password" autoComplete="current-password" value={deleteConfirm} onChange={event=>setDeleteConfirm(event.target.value)} disabled={busy}/></label><button className="danger-button" disabled={busy}>{busy?'Deleting account…':'Permanently delete my account'}</button></form>
    </div>
  </div>
}
