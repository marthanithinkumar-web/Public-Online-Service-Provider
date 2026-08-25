import React from 'react'

type FeeData={price_inr?:number;fee_inr?:number;official_fee_inr?:number|null;official_fee_status?:'known'|'none'|'unconfirmed'|string;total_fee_inr?:number|null}
const money=(value:number)=>`₹${new Intl.NumberFormat('en-IN',{maximumFractionDigits:2}).format(value)}`

export default function FeeSummary({data,compact=false}:{data:FeeData;compact?:boolean}){
  const assistance=Number(data.fee_inr??data.price_inr??0)
  const status=data.official_fee_status||'unconfirmed'
  const official=status==='none'?0:Number(data.official_fee_inr??0)
  const exact=status==='known'||status==='none'
  const total=data.total_fee_inr??(exact?assistance+official:null)
  return <section className={`fee-summary ${compact?'compact':''}`} aria-label="Fee summary">
    <div className="fee-summary-title"><h3>Fee Summary</h3><span>Clear charge breakdown</span></div>
    <dl><div><dt>Government / Official Fee</dt><dd>{exact?money(official):'To be confirmed'}</dd></div><div><dt>Our Assistance Fee</dt><dd>{money(assistance)}</dd></div><div className="fee-total"><dt>Total Payable</dt><dd>{total===null?'Calculated after the official fee is confirmed':money(Number(total))}</dd></div></dl>
    {exact&&<p className="fee-equation">{money(official)} + {money(assistance)} = <strong>{money(Number(total))}</strong></p>}
    {!compact&&<p className="fee-clarification">Our assistance fee covers application and service support. Government or official fees are separate, may vary by service, and are paid to the relevant authority where applicable. Payment does not guarantee approval.</p>}
  </section>
}
