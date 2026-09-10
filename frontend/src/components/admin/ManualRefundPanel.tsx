import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'

const methodLabel=(value:string)=>value==='upi'?'UPI':value==='bank_transfer'?'Bank Transfer':'Other'

export default function ManualRefundPanel({orderId,orderStatus}:{orderId:number,orderStatus:string}){
  const [summary,setSummary]=useState<any>(null)
  const [amount,setAmount]=useState('')
  const [method,setMethod]=useState('upi')
  const [reference,setReference]=useState('')
  const [refundedAt,setRefundedAt]=useState(()=>new Date().toISOString().slice(0,16))
  const [note,setNote]=useState('')
  const [proof,setProof]=useState<File|null>(null)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')

  const load=async()=>{try{const r=await axios.get(`${apiBase}/refunds/order/${orderId}`,{headers:authHeader(),timeout:15000});setSummary(r.data);if(!amount&&Number(r.data.remaining_refundable_inr||0)>0)setAmount(String(r.data.remaining_refundable_inr))}catch(e:any){setError(e?.response?.data?.error||'Unable to load refund records.')}}
  useEffect(()=>{load()},[orderId])

  const downloadProof=async(refund:any)=>{try{const response=await fetch(`${apiBase}/refunds/${refund.id}/proof`,{headers:authHeader()});if(!response.ok)throw new Error();const type=response.headers.get('content-type')||'';if(type.includes('application/json')){const body=await response.json();if(body.url){window.open(body.url,'_blank','noopener,noreferrer');return}throw new Error()}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=refund.proof_filename||'refund-proof';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{setError('Unable to download refund proof.')}}

  const record=async()=>{if(orderStatus!=='Cancelled')return;setBusy(true);setError('');setMessage('');try{const form=new FormData();form.append('amount_inr',amount);form.append('method',method);form.append('reference',reference.trim());form.append('refunded_at',new Date(refundedAt).toISOString());form.append('note',note.trim());if(proof)form.append('proof',proof);const r=await axios.post(`${apiBase}/refunds/order/${orderId}`,form,{headers:authHeader(),timeout:30000});setMessage(r.data.message||'Refund recorded successfully.');setReference('');setNote('');setProof(null);await load()}catch(e:any){setError(e?.response?.data?.error||'Unable to record refund.')}finally{setBusy(false)}}

  const refunds=summary?.refunds||[]
  const remaining=Number(summary?.remaining_refundable_inr||0)
  return <section className="dashboard-section" aria-labelledby="manual-refund-title">
    <span className="eyebrow">Manual refund record</span><h3 id="manual-refund-title">Refund proof & transaction history</h3>
    <p>Refunds are sent by you directly to the client outside Razorpay. This section only records the completed transfer and its proof.</p>
    {summary&&<div className="request-summary"><p><strong>Paid total:</strong> ₹{Number(summary.paid_total_inr||0).toFixed(2)}</p><p><strong>Refunded total:</strong> ₹{Number(summary.refunded_total_inr||0).toFixed(2)}</p><p><strong>Remaining refundable:</strong> ₹{remaining.toFixed(2)}</p><p><strong>Refund status:</strong> {String(summary.status||'not_refunded').replace(/_/g,' ')}</p></div>}
    {refunds.length>0&&<ul className="document-list">{refunds.map((refund:any)=><li key={refund.id}><span><strong>₹{Number(refund.amount_inr||0).toFixed(2)} refunded</strong><small>{new Date(refund.refunded_at).toLocaleString()} · {methodLabel(refund.method)}</small><small>Transaction reference: {refund.reference}</small>{refund.note&&<small>{refund.note}</small>}</span>{refund.proof_available&&<button type="button" className="btn-secondary" onClick={()=>downloadProof(refund)}>View refund proof</button>}</li>)}</ul>}
    {orderStatus!=='Cancelled'?<p className="info">Refund recording becomes available after the application is cancelled.</p>:remaining<=0?<p className="success-message">The recorded refundable amount has been fully refunded.</p>:<div className="request-form"><label>Refund amount (₹)<input type="number" min="0.01" max={remaining} step="0.01" value={amount} onChange={e=>setAmount(e.target.value)}/></label><label>Refund date & time<input type="datetime-local" value={refundedAt} max={new Date().toISOString().slice(0,16)} onChange={e=>setRefundedAt(e.target.value)}/></label><label>Payment method<select value={method} onChange={e=>setMethod(e.target.value)}><option value="upi">UPI</option><option value="bank_transfer">Bank Transfer</option><option value="other">Other</option></select></label><label>UTR / UPI / bank transaction reference<input value={reference} maxLength={160} onChange={e=>setReference(e.target.value)} placeholder="Enter the completed transfer reference"/></label><label>Optional note<textarea rows={3} maxLength={2000} value={note} onChange={e=>setNote(e.target.value)} placeholder="Example: Refund issued after client cancellation"/></label><label>Optional refund proof<input type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={e=>{const file=e.target.files?.[0]||null;if(file&&file.size>10*1024*1024){setError('Refund proof must be smaller than 10 MB.');setProof(null);return}setProof(file)}}/></label><small>Proof is private and available only to the admin and the client who owns this application.</small><button type="button" disabled={busy||!amount||reference.trim().length<3||!refundedAt} onClick={record}>{busy?'Recording refund…':'Confirm & record refund'}</button></div>}
    {error&&<p className="info" role="alert">{error}</p>}{message&&<p className="success-message" role="status">{message}</p>}
  </section>
}
