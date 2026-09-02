import React,{useEffect,useState} from 'react'
import {getPaymentStatus,openPaymentReceipt,payRequestTotal} from '../../services/payments'

export default function PaymentPanel({order}:{order:any}){
  const [state,setState]=useState<any>(null)
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')
  const refresh=async()=>{try{setState(await getPaymentStatus(Number(order.id)))}catch{}}
  useEffect(()=>{if(order?.id)refresh()},[order?.id])
  if(!order?.id)return null
  const payment=state?.payment
  const assistance=Number(state?.breakdown?.assistance_fee_inr??order?.fee_inr??0)
  const officialStatus=state?.breakdown?.official_fee_status??order?.official_fee_status??'unconfirmed'
  const official=state?.breakdown?.official_fee_inr==null?null:Number(state.breakdown.official_fee_inr)
  const total=state?.total_payable_inr==null?null:Number(state.total_payable_inr)
  const paid=payment?.status==='captured'||payment?.status==='paid'
  return <section className="dashboard-section payment-panel" aria-labelledby="request-payment-title">
    <span className="eyebrow">Secure online payment</span><h2 id="request-payment-title">Pay request charges</h2>
    <p>You pay once here. The amount combines our assistance fee with the confirmed official/government fee. We then use the official-fee portion for your application on the relevant official portal.</p>
    <div className="request-summary"><p><strong>Assistance fee:</strong> ₹{assistance.toFixed(2)}</p><p><strong>Official fee:</strong> {officialStatus==='unconfirmed'?'Waiting for confirmation':`₹${Number(official||0).toFixed(2)}`}</p>{total!=null&&<p><strong>Total payable:</strong> ₹{total.toFixed(2)}</p>}<p><strong>Status:</strong> {paid?'Paid':payment?.status==='authorized'?'Authorised — awaiting capture':payment?.status==='failed'?'Previous payment failed':'Not paid'}</p></div>
    {officialStatus==='unconfirmed'&&!paid&&<p className="info">The official fee is still being confirmed. Once the admin confirms it, you can pay the assistance fee and official fee together in one transaction.</p>}
    {paid&&<p className="success-message" role="status">Payment confirmed. A receipt is available here and is automatically emailed to the address on your request when SMTP delivery is configured.</p>}
    {message&&<p className="success-message" role="status">{message}</p>}{error&&<p className="info" role="alert">{error}</p>}
    <div className="cta-row">{!paid&&officialStatus!=='unconfirmed'&&total!=null&&total>0&&<button type="button" disabled={busy} onClick={async()=>{setBusy(true);setError('');setMessage('');try{const result:any=await payRequestTotal(order);setMessage(result?.status==='captured'?'Payment received successfully. Your receipt is now available.':'Payment authorised. Final confirmation will update automatically after capture.');setTimeout(refresh,2000)}catch(e:any){setError(e?.message||'Unable to complete payment.')}finally{setBusy(false)}}}>{busy?'Opening secure checkout…':`Pay ₹${total.toFixed(2)} with Razorpay`}</button>}{paid&&<button type="button" className="btn-secondary" disabled={busy} onClick={async()=>{setError('');try{await openPaymentReceipt(Number(order.id))}catch(e:any){setError(e?.message||'Unable to open payment receipt.')}}}>View / print receipt</button>}<button type="button" className="btn-secondary" disabled={busy} onClick={refresh}>Refresh payment status</button></div>
    <small>Enter OTPs, UPI PINs, card PINs and banking passwords only inside the Razorpay or bank payment screen. Never send them to the service provider.</small>
  </section>
}
