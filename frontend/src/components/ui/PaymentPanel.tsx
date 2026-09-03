import React,{useEffect,useState} from 'react'
import {emailPaymentReceipt,getPaymentStatus,openPaymentReceipt,payRequest,PaymentPurpose} from '../../services/payments'
import '../../styles/payment-panel.css'

const SCHOLARSHIP_SERVICE='Scholarship Application Assistance'

export default function PaymentPanel({order}:{order:any}){
  const [state,setState]=useState<any>(null)
  const [busy,setBusy]=useState<PaymentPurpose|null>(null)
  const [message,setMessage]=useState('')
  const [error,setError]=useState('')
  const refresh=async()=>{try{setState(await getPaymentStatus(Number(order.id)))}catch{}}
  useEffect(()=>{if(order?.id)refresh()},[order?.id])
  if(!order?.id)return null
  const scholarshipOnly=order?.service===SCHOLARSHIP_SERVICE||order?.application_data?.service_name===SCHOLARSHIP_SERVICE
  const assistance=Number(state?.breakdown?.assistance_fee_inr??order?.fee_inr??0)
  const officialStatus=scholarshipOnly?'none':(state?.breakdown?.official_fee_status??order?.official_fee_status??'unconfirmed')
  const official=scholarshipOnly?0:(state?.breakdown?.official_fee_inr==null?null:Number(state.breakdown.official_fee_inr))
  const total=scholarshipOnly?assistance:(state?.breakdown?.combined_total_inr==null?null:Number(state.breakdown.combined_total_inr))
  const assistancePaid=Boolean(state?.paid_components?.assistance_fee)
  const officialPaid=scholarshipOnly||Boolean(state?.paid_components?.official_fee)||officialStatus==='none'||official===0
  const capturedPayments=(state?.payments||[]).filter((item:any)=>item.status==='captured'||item.status==='paid')
  const runPayment=async(purpose:PaymentPurpose)=>{setBusy(purpose);setError('');setMessage('');try{const result:any=await payRequest(order,purpose);setMessage(result?.status==='captured'?'Payment received successfully. Your receipt is now available.':'Payment authorised. Final confirmation will update automatically after capture.');setTimeout(refresh,1800)}catch(e:any){setError(e?.message||'Unable to complete payment.')}finally{setBusy(null)}}
  const card=(purpose:PaymentPurpose,title:string,description:string,amount:number|null,disabled:boolean,paid:boolean,recommended=false)=><article className={`payment-option-card${recommended?' recommended':''}${paid?' paid':''}`}>
    {recommended&&<span className="payment-recommended">Recommended</span>}
    <h3>{title}</h3><p>{description}</p>
    <div className="payment-option-amount">{amount==null?'Waiting for confirmation':`₹${amount.toFixed(2)}`}</div>
    {paid?<span className="payment-paid-label">✓ Paid</span>:<button type="button" disabled={Boolean(busy)||disabled||amount==null||amount<=0} onClick={()=>runPayment(purpose)}>{busy===purpose?'Opening secure checkout…':title}</button>}
  </article>
  return <section className="dashboard-section payment-panel" aria-labelledby="request-payment-title">
    <span className="eyebrow">Secure online payment</span><h2 id="request-payment-title">Payment Options</h2>
    <p>{scholarshipOnly?'Scholarship applications use one payment option: our application assistance fee. There is no scholarship official-fee payment on this platform.':'Choose how you want to pay for this request. You can pay the assistance fee first, the official fee separately after it is confirmed, or pay both together when both are still due.'}</p>
    <div className="payment-options-grid">
      {card('assistance_fee','Pay Assistance Fee',scholarshipOnly?'Pay the scholarship application assistance fee.':'Pay only our assistance fee now.',assistance,assistancePaid,assistancePaid,scholarshipOnly)}
      {!scholarshipOnly&&card('official_fee','Pay Official Fee','Pay only the confirmed official/government fee.',official,officialStatus==='unconfirmed'||officialPaid,officialPaid)}
      {!scholarshipOnly&&card('request_total','Pay Total (Both Fees)','Pay the assistance fee and official fee together in one transaction.',total,officialStatus==='unconfirmed'||assistancePaid||officialPaid,assistancePaid&&officialPaid,!assistancePaid&&!officialPaid&&officialStatus!=='unconfirmed')}
    </div>
    <div className="payment-summary-box"><h3>Payment Summary</h3><div><span>Assistance fee</span><strong>₹{assistance.toFixed(2)}</strong></div>{!scholarshipOnly&&<><div><span>Official / Government fee</span><strong>{officialStatus==='unconfirmed'?'To be confirmed':`₹${Number(official||0).toFixed(2)}`}</strong></div><div className="payment-summary-total"><span>Total</span><strong>{total==null?'Confirmed later':`₹${total.toFixed(2)}`}</strong></div><small>You may pay fees individually or together for your convenience.</small></>}</div>
    {!scholarshipOnly&&officialStatus==='unconfirmed'&&!officialPaid&&<p className="info">The official fee is still being confirmed. You can pay the assistance fee now. Once the admin confirms the official fee, you can pay that fee separately.</p>}
    {message&&<p className="success-message" role="status">{message}</p>}{error&&<p className="info" role="alert">{error}</p>}
    {capturedPayments.length>0&&<div className="payment-receipts"><h3>Receipts</h3>{capturedPayments.map((payment:any)=><div className="payment-receipt-row" key={payment.id}><span>{String(payment.purpose||'payment').replace(/_/g,' ')} · ₹{Number(payment.amount_inr||0).toFixed(2)}</span><button type="button" className="btn-secondary" onClick={()=>openPaymentReceipt(Number(order.id),Number(payment.id))}>View / print receipt</button></div>)}</div>}
    <div className="cta-row">{capturedPayments.length>0&&<button type="button" className="btn-secondary" onClick={async()=>{setError('');try{const result=await emailPaymentReceipt(Number(order.id));setMessage(result.message||'Receipt emailed successfully.')}catch(e:any){setError(e?.response?.data?.error||e?.message||'Unable to email receipt.')}}}>Email latest receipt</button>}<button type="button" className="btn-secondary" disabled={Boolean(busy)} onClick={refresh}>Refresh payment status</button></div>
    <small>Enter OTPs, UPI PINs, card PINs and banking passwords only inside the Razorpay or bank payment screen. Never send them to the service provider.</small>
  </section>
}
