import React,{useEffect,useState} from 'react'
import {fetchAdminOverview,requestReportUrl} from '../../services/admin'
import {authHeader} from '../../services/auth'

export default function ActivityReports(){
 const [data,setData]=useState<any>({activity:[]}),[error,setError]=useState('')
 useEffect(()=>{fetchAdminOverview().then(setData).catch(()=>setError('Unable to load activity.'))},[])
 const download=async()=>{try{const r=await fetch(requestReportUrl(),{headers:authHeader()});if(!r.ok)throw new Error();const blob=await r.blob(),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='request-report.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{setError('Unable to download report.')}}
 return <div><div className="section-header"><div><span className="eyebrow">Audit and exports</span><h2>Activity & reports</h2><p>Review status activity and export the application register.</p></div><button onClick={download}>Download CSV report</button></div>{error&&<p className="info" role="alert">{error}</p>}<div className="dashboard-section"><h3>Recent status activity</h3><ul className="activity-list">{(data.activity||[]).map((a:any)=><li key={a.id}><strong>{a.previous_status||'Created'} → {a.new_status}</strong><small>{a.changed_by} · {a.note||'No note'} · {new Date(a.created_at).toLocaleString()}</small></li>)}</ul></div></div>
}
