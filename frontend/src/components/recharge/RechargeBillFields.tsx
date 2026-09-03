import React from 'react'
import {RECHARGE_BILL_TYPES,validIndianMobileNumber} from '../../services/rechargeBill'

type Props={answers:Record<string,string>;onChange:(key:string,value:string)=>void;error?:string}
const operators=['Airtel','Jio','Vi','BSNL']
const circles=['Andhra Pradesh','Assam','Bihar & Jharkhand','Delhi NCR','Gujarat','Haryana','Himachal Pradesh','Jammu & Kashmir','Karnataka','Kerala','Kolkata','Madhya Pradesh & Chhattisgarh','Maharashtra & Goa','Mumbai','North East','Odisha','Punjab','Rajasthan','Tamil Nadu','Telangana','Uttar Pradesh East','Uttar Pradesh West','West Bengal']

export function validateRechargeBillAnswers(a:Record<string,string>){
 const type=a.recharge_bill_type
 if(!type)return 'Choose a recharge or bill payment type.'
 if(type==='mobile_prepaid'||type==='mobile_postpaid'){
  if(!validIndianMobileNumber(a.customer_reference||''))return 'Enter a valid 10-digit Indian mobile number.'
  if(!a.operator)return 'Choose the mobile operator.'
  if(!a.circle)return 'Choose the telecom circle/state. Operator is not guessed from the mobile prefix because numbers can be ported.'
  if(type==='mobile_prepaid'&&!a.plan_reference?.trim())return 'Enter or select the exact recharge plan before continuing.'
 }
 if(!['mobile_prepaid','mobile_postpaid'].includes(type)&&!a.biller?.trim())return 'Enter or select the biller/provider.'
 if(!['mobile_prepaid'].includes(type)&&!a.customer_reference?.trim())return 'Enter the consumer/account/customer reference used by the provider.'
 return ''
}

export default function RechargeBillFields({answers,onChange}:Props){
 const type=answers.recharge_bill_type||''
 const mobile=type==='mobile_prepaid'||type==='mobile_postpaid'
 return <section className="dashboard-section" aria-labelledby="recharge-bill-details-title">
  <span className="eyebrow">Recharge & Bill Payments</span><h3 id="recharge-bill-details-title">Payment details</h3>
  <p>Choose the exact service and provide the identifiers used by the operator or biller. We never infer a mobile operator from the number prefix because mobile number portability can make that wrong.</p>
  <div className="admin-form service-admin-form">
   <label>Service type<select value={type} onChange={e=>onChange('recharge_bill_type',e.target.value)}><option value="">Choose service</option>{RECHARGE_BILL_TYPES.map(item=><option key={item.id} value={item.id}>{item.label}</option>)}</select></label>
   {mobile&&<><label>Mobile number<input inputMode="numeric" autoComplete="tel" maxLength={10} value={answers.customer_reference||''} onChange={e=>onChange('customer_reference',e.target.value.replace(/\D/g,'').slice(0,10))} placeholder="10-digit mobile number"/></label><label>Operator<select value={answers.operator||''} onChange={e=>onChange('operator',e.target.value)}><option value="">Choose operator</option>{operators.map(item=><option key={item}>{item}</option>)}</select></label><label>Circle / state<select value={answers.circle||''} onChange={e=>onChange('circle',e.target.value)}><option value="">Choose circle</option>{circles.map(item=><option key={item}>{item}</option>)}</select></label></>}
   {!mobile&&type&&<label>Biller / provider<input value={answers.biller||''} onChange={e=>onChange('biller',e.target.value)} placeholder="Provider shown on the bill"/></label>}
   {type==='mobile_prepaid'&&<><label>Recharge plan<input value={answers.plan_reference||''} onChange={e=>onChange('plan_reference',e.target.value)} placeholder="Exact plan amount/name from verified operator listing"/></label><label>Recharge amount (₹)<input type="number" min="1" step="0.01" value={answers.recharge_amount||''} onChange={e=>onChange('recharge_amount',e.target.value)} placeholder="Plan amount"/></label></>}
   {type&&type!=='mobile_prepaid'&&<><label>Consumer / account / customer reference<input value={answers.customer_reference||''} onChange={e=>onChange('customer_reference',e.target.value)} placeholder="As printed by the provider"/></label><label>Bill / recharge amount (₹)<input type="number" min="0" step="0.01" value={answers.recharge_amount||''} onChange={e=>onChange('recharge_amount',e.target.value)} placeholder="Amount shown by provider"/></label></>}
  </div>
  <div className="service-safety-banner"><strong>Do not enter OTPs, UPI PINs, card PINs, CVV, passwords or banking credentials here.</strong> Until an authorised payment/recharge integration is connected, a submitted request is assistance/tracking only and is not represented as a completed operator recharge or bill settlement.</div>
 </section>
}
