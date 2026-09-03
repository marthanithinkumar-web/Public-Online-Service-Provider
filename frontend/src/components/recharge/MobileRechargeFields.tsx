import React from 'react'
import {MOBILE_OPERATORS,normalizeIndianMobileNumber,RechargeAnswers} from '../../services/rechargeBill'

type Props={answers:RechargeAnswers;onChange:(key:string,value:string)=>void}

const CIRCLES=['Andhra Pradesh','Assam','Bihar & Jharkhand','Chennai','Delhi NCR','Gujarat','Haryana','Himachal Pradesh','Jammu & Kashmir','Karnataka','Kerala','Kolkata','Madhya Pradesh & Chhattisgarh','Maharashtra & Goa','Mumbai','North East','Odisha','Punjab','Rajasthan','Tamil Nadu','Telangana','Uttar Pradesh East','Uttar Pradesh West & Uttarakhand','West Bengal']

export default function MobileRechargeFields({answers,onChange}:Props){
 return <section className="dashboard-section" aria-labelledby="mobile-recharge-details">
  <div className="section-header"><div><span className="eyebrow">Recharge details</span><h3 id="mobile-recharge-details">Mobile Recharge</h3><p>Choose the operator and exact plan for the number you want to recharge.</p></div></div>
  <div className="form-grid">
   <label>Mobile number<input inputMode="numeric" autoComplete="tel" maxLength={13} value={answers.mobile_number||''} onChange={e=>onChange('mobile_number',normalizeIndianMobileNumber(e.target.value))} placeholder="10-digit mobile number"/></label>
   <label>Operator<select value={answers.operator||''} onChange={e=>onChange('operator',e.target.value)}><option value="">Select operator</option>{MOBILE_OPERATORS.map(x=><option key={x} value={x}>{x}</option>)}</select></label>
   <label>Circle / state<select value={answers.circle||''} onChange={e=>onChange('circle',e.target.value)}><option value="">Select circle / state</option>{CIRCLES.map(x=><option key={x} value={x}>{x}</option>)}</select></label>
   <label>Recharge plan<input value={answers.plan_reference||''} onChange={e=>onChange('plan_reference',e.target.value)} placeholder="Example: 28 days / 1.5 GB per day"/></label>
   <label>Recharge amount (₹)<input type="number" inputMode="decimal" min="1" max="100000" step="0.01" value={answers.recharge_amount??''} onChange={e=>onChange('recharge_amount',e.target.value)} placeholder="Plan amount"/></label>
  </div>
  <div className="info"><strong>Important:</strong> Select the operator yourself; the website does not guess it from the phone-number prefix because mobile numbers can be ported. Never enter an OTP, UPI PIN, card PIN/CVV, banking password or operator-account password here.</div>
  <p className="muted">The recharge amount is separate from the website assistance fee. Until an authorised recharge integration is connected, this request records assistance and tracking and does not claim that the operator recharge has already been completed.</p>
 </section>
}
