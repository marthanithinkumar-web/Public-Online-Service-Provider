import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {apiBase} from '../../services/apiBase'
import {authHeader} from '../../services/auth'

const methodLabel=(value:string)=>value==='upi'?'UPI':value==='bank_transfer'?'Bank Transfer':'Other'

export default function RefundStatus({orderId}:{orderId:number}){
  const [summary,setSummary]=useState<any>(null)
  const [error,setError]=useState('')
  const load=async()=>{try{const r=await axios.get(`${apiBase}/refunds/order/${orderId}`,{headers:authHeader(),timeout:15000});setSummary(r.data)}catch(e:any){setError(e?.response?.data?.error||'Unable to load refund status.')}}
  useEffect(()=>{load()},[orderId])
  const downloadProof=async(refund:any)=>{try{const response=await fetch(`${apiBase}/refunds/${refund.id}/proof`,{headers:authHeader()});if(!response.ok)throw new Error();const type=response.headers.get('content-type')||'';if(type.includes('application/json')){const body=await response.json();if(body.url){window.open(body.url,'_blank','noopener,noreferrer');return}throw new Error()}const blob=await response.blob(),url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download=refund.proof_filename||'refund-proof';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}catch{setError('Refund proof could not be downloaded.')}}
  if(!summary||(!summary.refunds?.length&&!error))return null
  return <section className="dashboard-section"><h2>Refund status</h2>{summary&&<div className="request-summary"><p><strong>Status:</strong> {String(summary.status||'not_refunded').replace(/_/g,' ')}</p><p><strong>Total refunded:</strong> ₹{Number(summary.refunded_total_inr||0).toFixed(2)}</p>{Number(summary.remaining_refundable_inr||0)>0&&<p><strong>Remaining refundable:</strong> ₹{Number(summary.remaining_refundable_inr).toFixed(2)}</p>}</div>}{summary?.refunds?.length>0&&<ul className="document-list">{summary.refunds.map((refund:any)=><li key={refund.id}><span><strong>₹{Number(refund.amount_inr||0).toFixed(2)} refunded</strong><small>{new Date(refund.refunded_at).toLocaleString()} · {methodLabel(refund.method)}</small><small>Transaction reference: {refund.reference}</small>{refund.note&&<small>{refund.note}</small>}</span>{refund.proof_available&&<button type="button" className="btn-secondary" onClick={()=>downloadProof(refund)}>View refund proof</button>}</li>)}</ul>}{error&&<p className="info" role="alert">{error}</p>}</section>
}
