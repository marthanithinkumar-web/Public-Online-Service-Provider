import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {apiBase} from '../../services/apiBase'
import {authHeader} from '../../services/auth'

type Props={order:any}

export default function WhatsAppStatusUpdates({order}:Props){
  const [available,setAvailable]=useState(false)
  const [enabled,setEnabled]=useState(String(order?.contact_method||'').toLowerCase()==='whatsapp')
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')

  useEffect(()=>{setEnabled(String(order?.contact_method||'').toLowerCase()==='whatsapp')},[order?.id,order?.contact_method])
  useEffect(()=>{
    let active=true
    axios.get(`${apiBase}/whatsapp/config`,{timeout:10000})
      .then(response=>{if(active)setAvailable(Boolean(response.data?.status_notifications_available))})
      .catch(()=>{if(active)setAvailable(false)})
    return()=>{active=false}
  },[])

  if(!available||!order?.id)return null
  const terminal=['Completed','Cancelled','Rejected'].includes(order.status)

  const updatePreference=async(next:boolean)=>{
    if(busy)return
    setBusy(true);setMessage('')
    try{
      const response=await axios.post(`${apiBase}/whatsapp/orders/${order.id}/preference`,{enabled:next},{headers:authHeader(),timeout:12000})
      setEnabled(Boolean(response.data?.enabled))
      setMessage(response.data?.message||'WhatsApp preference updated.')
    }catch(error:any){
      setMessage(error?.response?.data?.error||'Unable to update WhatsApp status notifications. Please try again.')
    }finally{setBusy(false)}
  }

  return <section className="dashboard-section" aria-labelledby="whatsapp-status-heading">
    <span className="eyebrow">Optional</span>
    <h2 id="whatsapp-status-heading">WhatsApp status updates</h2>
    <p>Receive important updates for this request on the phone number saved with the application. You can turn this off at any time. Standard website and email updates continue separately.</p>
    <p className="auth-hint">We use WhatsApp only for request-related updates you choose to receive. Never share passwords, OTPs, PINs, CVV details or banking credentials in WhatsApp.</p>
    <div className="cta-row">
      {enabled?<button type="button" className="btn btn-secondary" disabled={busy} onClick={()=>updatePreference(false)}>{busy?'Updating…':'Turn off WhatsApp updates'}</button>:<button type="button" className="btn btn-whatsapp" disabled={busy||terminal} onClick={()=>updatePreference(true)}>{busy?'Updating…':terminal?'Request already closed':'Enable WhatsApp updates'}</button>}
      <strong aria-live="polite">{enabled?'WhatsApp updates: On':'WhatsApp updates: Off'}</strong>
    </div>
    {message&&<p className="info" role="status">{message}</p>}
  </section>
}
