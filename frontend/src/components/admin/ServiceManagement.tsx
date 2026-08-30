import React,{useEffect,useMemo,useState} from 'react'
import {
  createCategory,createService,fetchCategories,fetchServices,setServiceActive,
  fetchHomepageAssistanceFee,updateAllAssistanceFees,updateHomepageAssistanceFee,updateService,
} from '../../services/admin'
import FeeSummary from '../ui/FeeSummary'

type OfficialStatus='known'|'none'|'unconfirmed'

export default function ServiceManagement(){
  const [services,setServices]=useState<any[]>([])
  const [categories,setCategories]=useState<any[]>([])
  const [name,setName]=useState('')
  const [desc,setDesc]=useState('')
  const [keywords,setKeywords]=useState('')
  const [categoryId,setCategoryId]=useState('')
  const [newCategory,setNewCategory]=useState('')
  const [price,setPrice]=useState(30)
  const [officialStatus,setOfficialStatus]=useState<OfficialStatus>('unconfirmed')
  const [officialFee,setOfficialFee]=useState<number|''>('')
  const [editing,setEditing]=useState<number|null>(null)
  const [globalFee,setGlobalFee]=useState<number|''>(30)
  const [globalConfirmed,setGlobalConfirmed]=useState(false)
  const [homepageFee,setHomepageFee]=useState<number|''>(30)
  const [error,setError]=useState('')
  const [message,setMessage]=useState('')
  const [busy,setBusy]=useState(false)

  const load=async()=>{
    try{
      setError('')
      const [serviceItems,categoryItems,homepageFeeResult]=await Promise.all([fetchServices(),fetchCategories(),fetchHomepageAssistanceFee()])
      setServices(serviceItems)
      setCategories(categoryItems)
      setHomepageFee(Number(homepageFeeResult.price_inr))
      const feeValues=Array.from(new Set(serviceItems.map((service:any)=>Number(service.price_inr||0))))
      if(feeValues.length===1){
        setGlobalFee(feeValues[0] as number)
        if(editing===null)setPrice(feeValues[0] as number)
      }
    }catch{
      setError('Unable to load services or categories.')
    }
  }
  useEffect(()=>{load()},[])

  const currentFeeText=useMemo(()=>{
    const values=Array.from(new Set(services.map(service=>Number(service.price_inr||0)))).sort((a,b)=>a-b)
    if(!values.length)return 'No services'
    if(values.length===1)return `₹${values[0]}`
    return `Different fees: ₹${values.join(', ₹')}`
  },[services])

  const reset=()=>{
    setName('');setDesc('');setKeywords('');setCategoryId('');setPrice(globalFee===''?0:Number(globalFee))
    setOfficialStatus('unconfirmed');setOfficialFee('');setEditing(null)
  }

  const save=async()=>{
    try{
      setBusy(true);setError('');setMessage('')
      if(price<0){setError('Assistance fee cannot be negative.');return}
      if(officialStatus==='known'&&(officialFee===''||Number(officialFee)<0)){
        setError('Enter the confirmed official fee.');return
      }
      const payload={
        name,description:desc,keywords,category_id:categoryId?Number(categoryId):null,
        price_inr:price,official_fee_status:officialStatus,
        official_fee_inr:officialStatus==='known'?Number(officialFee):officialStatus==='none'?0:null,
      }
      if(editing)await updateService(editing,payload);else await createService(payload)
      setMessage(editing?'Service updated successfully.':'Service added successfully.')
      reset();await load()
    }catch(err:any){
      const value=err?.response?.data?.error
      setError(typeof value==='string'?value:'Unable to save service.')
    }finally{setBusy(false)}
  }

  const updateWebsiteFee=async()=>{
    const value=Number(globalFee)
    if(globalFee===''||!Number.isFinite(value)||value<0){setError('Enter a valid assistance fee.');return}
    if(!globalConfirmed){setError('Confirm that you understand this changes all current service fees.');return}
    if(!window.confirm(`Change the assistance fee for all ${services.length} services to ₹${value}? Existing submitted requests will keep their original fee.`))return
    try{
      setBusy(true);setError('');setMessage('')
      const result=await updateAllAssistanceFees(value)
      setMessage(`${result.message} Existing submitted requests were not repriced.`)
      setGlobalConfirmed(false)
      await load()
    }catch(err:any){
      setError(err?.response?.data?.error||'Unable to update the website-wide assistance fee.')
    }finally{setBusy(false)}
  }

  const saveHomepageFee=async()=>{
    const value=Number(homepageFee)
    if(homepageFee===''||!Number.isFinite(value)||value<0){setError('Enter a valid homepage assistance fee.');return}
    try{
      setBusy(true);setError('');setMessage('')
      const result=await updateHomepageAssistanceFee(value)
      setMessage(`${result.message} Individual service fees were not changed.`)
    }catch(err:any){setError(err?.response?.data?.error||'Unable to update the homepage assistance fee.')}
    finally{setBusy(false)}
  }

  const addCategory=async()=>{
    const value=newCategory.trim();if(value.length<2)return
    try{
      setBusy(true);setError('')
      const result=await createCategory(value)
      setNewCategory('');await load()
      if(result.category?.id)setCategoryId(String(result.category.id))
      setMessage('Category added successfully.')
    }catch(err:any){setError(err?.response?.data?.error||'Unable to add category.')}
    finally{setBusy(false)}
  }

  const edit=(service:any)=>{
    setEditing(service.id);setName(service.name);setDesc(service.description||'')
    setKeywords(service.keywords||'');setCategoryId(service.category_id?String(service.category_id):'')
    setPrice(service.price_inr??0);setOfficialStatus(service.official_fee_status||'unconfirmed')
    setOfficialFee(service.official_fee_inr??'');window.scrollTo({top:0,behavior:'smooth'})
  }

  const toggle=async(service:any)=>{
    try{
      setError('');await setServiceActive(service.id,!service.is_active)
      setMessage(`Service ${service.is_active?'disabled':'enabled'} successfully.`);await load()
    }catch{setError('Unable to update service availability.')}
  }

  return <div>
    <div className="section-header"><div><h2>Services & fees</h2></div></div>
    {error&&<p className="info" role="alert">{error}</p>}
    {message&&<p className="success-message" role="status">{message}</p>}

    <section className="dashboard-section global-fee-card" aria-labelledby="homepage-fee-title">
      <div>
        <span className="eyebrow">Homepage pricing display</span>
        <h3 id="homepage-fee-title">Homepage Applicable Assistance Fee</h3>
      </div>
      <div className="global-fee-controls">
        <label>Applicable Assistance Fee (₹)<input type="number" min="0" max="100000" step="0.01" value={homepageFee} onChange={e=>setHomepageFee(e.target.value===''?'':Number(e.target.value))}/></label>
        <button type="button" disabled={busy||homepageFee===''} onClick={saveHomepageFee}>{busy?'Saving…':'Save homepage fee'}</button>
      </div>
    </section>

    <section className="dashboard-section global-fee-card" aria-labelledby="global-fee-title">
      <div>
        <span className="eyebrow">Website-wide pricing</span>
        <h3 id="global-fee-title">All service fees</h3>
        <p className="global-fee-current"><strong>Current catalog:</strong> {currentFeeText}</p>
      </div>
      <div className="global-fee-controls">
        <label>Applicable Assistance Fee (₹)<input type="number" min="0" max="100000" step="0.01" value={globalFee} onChange={e=>setGlobalFee(e.target.value===''?'':Number(e.target.value))}/></label>
        <label className="fee-acknowledgement"><input type="checkbox" checked={globalConfirmed} onChange={e=>setGlobalConfirmed(e.target.checked)}/> I understand this replaces the current assistance fee on every service. Existing submitted requests keep their original agreed fee.</label>
        <button type="button" disabled={busy||!globalConfirmed||globalFee===''} onClick={updateWebsiteFee}>{busy?'Updating fees…':'Update fee across website'}</button>
        <small>This is your private assistance charge. It is never presented as a government or official fee.</small>
      </div>
    </section>

    <div className="dashboard-section admin-form service-admin-form">
      <label>Service name<input placeholder="Service name" value={name} onChange={e=>setName(e.target.value)}/></label>
      <label>Description<textarea rows={4} placeholder="Purpose and assistance provided" value={desc} onChange={e=>setDesc(e.target.value)}/></label>
      <label>Category<select value={categoryId} onChange={e=>setCategoryId(e.target.value)}><option value="">Select category</option>{categories.map(category=><option key={category.id} value={category.id}>{category.name}</option>)}</select></label>
      <div className="inline-admin-field"><label>New category<input placeholder="Add a category" value={newCategory} onChange={e=>setNewCategory(e.target.value)}/></label><button type="button" className="btn-secondary" disabled={busy||newCategory.trim().length<2} onClick={addCategory}>Add category</button></div>
      <label>Search keywords / tags<textarea rows={3} placeholder="Comma-separated terms clients may search" value={keywords} onChange={e=>setKeywords(e.target.value)}/><small>Include useful variations only. Example: income, residence, certificate, application.</small></label>
      <label>Applicable Assistance Fee (₹)<input type="number" min="0" step="0.01" value={price} onChange={e=>setPrice(Number(e.target.value))}/></label>
      <label>Government / official fee status<select value={officialStatus} onChange={e=>setOfficialStatus(e.target.value as OfficialStatus)}><option value="unconfirmed">To be confirmed</option><option value="none">No official fee</option><option value="known">Known exact amount</option></select></label>
      {officialStatus==='known'&&<label>Government / official fee (₹)<input type="number" min="0" step="0.01" value={officialFee} onChange={e=>setOfficialFee(e.target.value===''?'':Number(e.target.value))}/></label>}
      <FeeSummary data={{price_inr:price,official_fee_status:officialStatus,official_fee_inr:officialStatus==='known'?Number(officialFee):officialStatus==='none'?0:null}} compact/>
      <div className="button-row"><button type="button" disabled={busy||name.trim().length<2} onClick={save}>{busy?'Saving…':editing?'Save changes':'Add service'}</button>{editing&&<button type="button" className="btn-secondary" onClick={reset}>Cancel edit</button>}</div>
    </div>

    <ul className="admin-service-list">{services.map(service=><li key={service.id}><div><strong>{service.name}</strong><p>{service.description}</p><small>Category: {service.category||'Not assigned'} · {service.is_active?'Active':'Disabled'}</small>{service.keywords&&<small className="service-keywords">Search terms: {service.keywords}</small>}</div><FeeSummary data={service} compact/><div className="button-row"><button onClick={()=>edit(service)}>Edit</button><button className="btn-secondary" onClick={()=>toggle(service)}>{service.is_active?'Disable':'Enable'}</button></div></li>)}</ul>
  </div>
}
