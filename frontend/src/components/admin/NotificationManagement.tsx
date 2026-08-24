import React,{useEffect,useState} from 'react'
import {fetchAdminUsers,sendClientNotification} from '../../services/admin'

export default function NotificationManagement(){
 const [users,setUsers]=useState<any[]>([]),[userId,setUserId]=useState(''),[title,setTitle]=useState(''),[message,setMessage]=useState(''),[status,setStatus]=useState(''),[busy,setBusy]=useState(false)
 useEffect(()=>{fetchAdminUsers(1,'').then(r=>setUsers(r.items||[])).catch(()=>setStatus('Unable to load clients.'))},[])
 const submit=async(e:React.FormEvent)=>{e.preventDefault();setBusy(true);setStatus('');try{await sendClientNotification({user_id:Number(userId),title,message});setTitle('');setMessage('');setStatus('Notification sent successfully.')}catch(e:any){setStatus(e?.response?.data?.error||'Unable to send notification.')}finally{setBusy(false)}}
 return <div><div className="section-header"><div><span className="eyebrow">Client communication</span><h2>Send notification</h2><p>Send important service updates without requesting passwords, OTPs or banking information.</p></div></div><form className="dashboard-section admin-form" onSubmit={submit}><label>Client<select required value={userId} onChange={e=>setUserId(e.target.value)}><option value="">Select client</option>{users.map(u=><option value={u.id} key={u.id}>{u.name||u.email} — {u.email}</option>)}</select></label><label>Title<input required maxLength={200} value={title} onChange={e=>setTitle(e.target.value)}/></label><label>Message<textarea required rows={6} maxLength={4000} value={message} onChange={e=>setMessage(e.target.value)}/></label>{status&&<p className="info" role="status">{status}</p>}<button disabled={busy}>{busy?'Sending…':'Send notification'}</button></form></div>
}
