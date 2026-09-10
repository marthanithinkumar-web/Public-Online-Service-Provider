import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {authHeader} from '../../services/auth'
import {apiBase} from '../../services/apiBase'
import {clearServiceCatalog} from '../../services/serviceCatalog'

const api=axios.create({baseURL:apiBase,timeout:15000})

export default function RechargeBillFeeManagement({embedded=false}:{embedded?:boolean}){
  const [fee,setFee]=useState<number|''>('')
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')

  const load=async()=>{
    try{
      setError('')
      const response=await api.get('/fees/recharge-bill-assistance',{headers:authHeader()})
      setFee(Number(response.data?.price_inr??10))
    }catch{
      setError('Unable to load the Recharge & Bill Payments assistance fee.')
    }
  }

  useEffect(()=>{load()},[])

  const save=async()=>{
    const value=Number(fee)
    if(fee===''||!Number.isFinite(value)||value<0||value>100000){
      setError('Enter a valid Recharge & Bill Payments assistance fee from ₹0 to ₹1,00,000.')
      return
    }
    try{
      setBusy(true);setError('');setMessage('')
      const response=await api.put('/fees/recharge-bill-assistance',{price_inr:value},{headers:authHeader()})
      setFee(Number(response.data?.price_inr??value))
      clearServiceCatalog()
      setMessage(`${response.data?.message||'Recharge & Bill Payments assistance fee updated.'} Existing submitted requests keep their original agreed fee.`)
    }catch(err:any){
      setError(err?.response?.data?.error||'Unable to update the Recharge & Bill Payments assistance fee.')
    }finally{
      setBusy(false)
    }
  }

  return <div>
    {!embedded&&<div className="section-header"><div><h2>Recharge & Bill Payments Fees</h2><p>Manage the assistance fee used for new recharge and bill-payment requests.</p></div></div>}
    {error&&<p className="info" role="alert">{error}</p>}
    {message&&<p className="success-message" role="status">{message}</p>}
    <section className="dashboard-section global-fee-card" aria-labelledby="recharge-bill-fee-title">
      <div>
        <span className="eyebrow">Website-wide pricing</span>
        <h3 id="recharge-bill-fee-title">Recharge & Bill Payments Assistance Fee</h3>
        <p className="global-fee-current">This fee applies to new Mobile Recharge, Mobile Postpaid, DTH, Broadband / Landline, FASTag and Piped Gas assistance requests. Existing submitted requests keep their already agreed fee.</p>
      </div>
      <div className="global-fee-controls">
        <label>Recharge & Bill Payments Assistance Fee (₹)<input type="number" min="0" max="100000" step="0.01" value={fee} onChange={e=>setFee(e.target.value===''?'':Number(e.target.value))}/></label>
        <button type="button" disabled={busy||fee===''} onClick={save}>{busy?'Saving…':'Save recharge & bill fee'}</button>
        <small>₹0 is allowed. Changes apply to future requests across all supported recharge and bill-payment services. Government / official charges remain separate and are shown as “To be confirmed”.</small>
      </div>
    </section>
  </div>
}
