import React,{useEffect,useState} from 'react'
import {fetchAdminProfile,updateAdminProfile} from '../../services/admin'
import {saveToken} from '../../services/localStorage'

export default function AdminSettings(){
 const [name,setName]=useState(''),[email,setEmail]=useState(''),[phone,setPhone]=useState(''),[currentPassword,setCurrentPassword]=useState(''),[newPassword,setNewPassword]=useState(''),[status,setStatus]=useState(''),[busy,setBusy]=useState(false)
 useEffect(()=>{fetchAdminProfile().then(r=>{setName(r.user.name||'');setEmail(r.user.email||'');setPhone(r.user.phone||'')}).catch(()=>setStatus('Unable to load admin profile.'))},[])
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setStatus('');try{const result=await updateAdminProfile({name,phone,current_password:currentPassword,new_password:newPassword});if(result.token)saveToken(result.token);setCurrentPassword('');setNewPassword('');setStatus('Profile updated successfully.')}catch(e:any){setStatus(e?.response?.data?.error||'Unable to update profile.')}finally{setBusy(false)}}
 return <div><div className="section-header"><div><span className="eyebrow">Administrator account</span><h2>Profile & settings</h2></div></div><form className="dashboard-section admin-form" onSubmit={submit}><label>Name<input required value={name} onChange={e=>setName(e.target.value)}/></label><label>Email<input disabled value={email}/></label><label>Phone<input value={phone} onChange={e=>setPhone(e.target.value)}/></label><h3>Change password (optional)</h3><label>Current password<input type="password" autoComplete="current-password" value={currentPassword} onChange={e=>setCurrentPassword(e.target.value)}/></label><label>New password<input type="password" minLength={8} autoComplete="new-password" value={newPassword} onChange={e=>setNewPassword(e.target.value)}/></label>{status&&<p className="info" role="status">{status}</p>}<button disabled={busy}>{busy?'Saving…':'Save settings'}</button></form></div>
}
