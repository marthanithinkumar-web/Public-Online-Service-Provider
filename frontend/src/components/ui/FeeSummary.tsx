import React from 'react'

type FeeData={price_inr?:number;fee_inr?:number;official_fee_inr?:number|null;official_fee_status?:'known'|'none'|'unconfirmed'|string;total_fee_inr?:number|null}
const money=(value:number)=>`₹${new Intl.NumberFormat('en-IN',{maximumFractionDigits:2}).format(value)}`

export default function FeeSummary({data,compact=false}:{data:FeeData;compact?:boolean}){
  const assistance=Number(data.fee_inr??data.price_inr??0)
  return <section className={`fee-summary ${compact?'compact':''}`} aria-label="Fee summary">
    <div className="fee-summary-title"><h3>Fees</h3></div>
    <dl><div><dt>Applicable Assistance Fee</dt><dd>{money(assistance)}</dd></div><div><dt>Government / Official Fee</dt><dd>To be confirmed</dd></div><div className="fee-total"><dt>Total</dt><dd>Confirmed later</dd></div></dl>
    {!compact&&<p className="fee-clarification">Government or official fees are separate and will be confirmed before payment.</p>}
  </section>
}
