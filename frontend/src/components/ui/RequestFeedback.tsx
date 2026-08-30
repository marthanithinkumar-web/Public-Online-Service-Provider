import React,{useEffect,useMemo,useState} from 'react'
import axios from 'axios'
import {apiBase} from '../../services/apiBase'
import {authHeader} from '../../services/auth'

export default function RequestFeedback({orders,fixedOrderId,onSubmitted}:{orders?:any[];fixedOrderId?:number;onSubmitted?:()=>void}){
 const [reviewed,setReviewed]=useState<number[]>([]);const [orderId,setOrderId]=useState(fixedOrderId?String(fixedOrderId):'');const [rating,setRating]=useState(5);const [comment,setComment]=useState('');const [busy,setBusy]=useState(false);const [message,setMessage]=useState('');const [error,setError]=useState('')
 useEffect(()=>{axios.get(`${apiBase}/reviews/mine`,{headers:authHeader(),timeout:12000}).then(r=>setReviewed((r.data?.items||[]).map((item:any)=>Number(item.order_id)))).catch(()=>{})},[])
 const available=useMemo(()=>(orders||[]).filter(order=>!reviewed.includes(Number(order.id))),[orders,reviewed])
 if(fixedOrderId&&reviewed.includes(Number(fixedOrderId)))return <p className="success-message">Feedback submitted. Thank you.</p>
 const submit=async(e:React.FormEvent)=>{e.preventDefault();if(!orderId||busy)return;setBusy(true);setError('');setMessage('');try{const r=await axios.post(`${apiBase}/reviews/`,{order_id:Number(orderId),rating,comment:comment.trim()||null},{headers:authHeader(),timeout:12000});setReviewed(items=>[...items,Number(orderId)]);setMessage(r.data.message);setComment('');if(!fixedOrderId)setOrderId('');onSubmitted?.()}catch(err:any){setError(err?.response?.data?.error||'Unable to send feedback.')}finally{setBusy(false)}}
 if(!fixedOrderId&&!available.length)return null
 return <form className="request-feedback" onSubmit={submit}><h3>Rating & suggestions</h3>{!fixedOrderId&&<label>Request<select required value={orderId} onChange={e=>setOrderId(e.target.value)}><option value="">Select request</option>{available.map(order=><option value={order.id} key={order.id}>{order.order_code} — {order.service}</option>)}</select></label>}<fieldset><legend>Rating</legend><div className="rating-options">{[1,2,3,4,5].map(value=><label key={value}><input type="radio" name={`rating-${fixedOrderId||'dashboard'}`} value={value} checked={rating===value} onChange={()=>setRating(value)}/><span>{value}★</span></label>)}</div></fieldset><label>Suggestion<textarea rows={3} maxLength={2000} value={comment} onChange={e=>setComment(e.target.value)} placeholder="Tell us what we can improve"/></label>{error&&<p className="info" role="alert">{String(error)}</p>}{message&&<p className="success-message" role="status">{message}</p>}<button type="submit" disabled={busy||!orderId}>{busy?'Sending…':'Send feedback'}</button></form>
}
