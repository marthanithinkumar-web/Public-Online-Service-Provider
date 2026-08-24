import React,{useEffect,useState} from 'react'
import {fetchAdminDocuments} from '../../services/admin'
import {apiBase} from '../../services/apiBase'
import {authHeader} from '../../services/auth'

export default function DocumentManagement(){
 const [items,setItems]=useState<any[]>([]),[page,setPage]=useState(1),[meta,setMeta]=useState<any>({}),[error,setError]=useState('')
 useEffect(()=>{fetchAdminDocuments(page).then(r=>{setItems(r.items||[]);setMeta(r.meta||{})}).catch(()=>setError('Unable to load documents.'))},[page])
 const download=async(a:any)=>{setError('');try{const r=await fetch(`${apiBase}/uploads/${a.id}/download`,{headers:authHeader()});if(!r.ok)throw new Error();const type=r.headers.get('content-type')||'';if(type.includes('application/json')){const d=await r.json();window.open(d.url,'_blank','noopener,noreferrer');return}const blob=await r.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=a.filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{setError('Document download failed.')}}
 return <div><div className="section-header"><div><span className="eyebrow">Secure files</span><h2>Document management</h2><p>Documents uploaded against client requests.</p></div></div>{error&&<p className="info" role="alert">{error}</p>}<div className="card-list">{items.map(a=><article className="action-card" key={a.id}><strong>{a.filename}</strong><small>{a.order_code||'No request'} · {a.client_name||'Unknown client'} · {new Date(a.created_at).toLocaleString()}</small><button onClick={()=>download(a)}>Download securely</button></article>)}</div><div className="pagination"><button disabled={page<=1} onClick={()=>setPage(p=>p-1)}>Previous</button><span>Page {meta.page||1} of {meta.pages||1}</span><button disabled={page>=(meta.pages||1)} onClick={()=>setPage(p=>p+1)}>Next</button></div></div>
}
