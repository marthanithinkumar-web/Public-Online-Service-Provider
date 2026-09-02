import React,{useEffect,useState} from 'react'
import {getPaymentStatus,payAssistanceFee} from '../../services/payments'

export default function PaymentPanel({order}:{order:any}){
  const [payment,setPayment]=useState<any>(null)
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')
  const amount=Number(order?.fee_inr||0)
  const paid=payment?.status==='captured'||payment?.status==='paid'

  const refresh=async()=>{try{setPayment(await getPaymentStatus(Number(order.id)))}catch{}}
  useEffect(()=>{if(order?.id)refresh()},[order?.id])

  if(!order?.id||amount<=0)return null
  return <section className="dashboard-section payment-panel" aria-labelledby="assistance-payment-title">
    <span className="eyebrow">Secure online payment</span>
    <h2 id="assistance-payment-title">Applicable Assistance Fee</h2>
    <p>This payment is only for the private assistance fee shown for this request. Any government or official fee is separate and is not collected here unless it is explicitly added later with your approval.</p>
    <div className="request-summary"><p><strong>Amount:</strong> ₹{amount.toFixed(2)}</p><p><strong>Status:</strong> {paid?'Paid':payment?.status==='authorized'?'Authorised — awaiting capture':payment?.status==='failed'?'Previous payment failed':'Not paid'}</p></div>
    {message&&<p className="success-message" role="status">{message}</p>}
    {error&&<p className="info" role="alert">{error}</p>}
    <div className="cta-row">
      {!paid&&<button type="button" disabled={busy} onClick={async()=>{setBusy(true);setError('');setMessage('');try{const result:any=await payAssistanceFee(order);setPayment(result);setMessage(result?.status==='captured'?'Payment received successfully.':'Payment authorised. Final confirmation will update automatically after capture.');setTimeout(refresh,2500)}catch(e:any){setError(e?.message||'Unable to complete payment.')}finally{setBusy(false)}}}>{busy?'Opening secure checkout…':`Pay ₹${amount.toFixed(2)} with Razorpay`}</button>}
      <button type="button" className="btn-secondary" disabled={busy} onClick={refresh}>Refresh payment status</button>
    </div>
    <small>Do not share OTPs, UPI PINs, card PINs or banking passwords with the service provider. Enter payment authentication only inside the Razorpay/bank payment screen.</small>
  </section>
}
