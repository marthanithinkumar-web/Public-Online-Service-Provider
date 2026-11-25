import React,{useEffect,useRef,useState} from 'react'
import {streamAiBenchmark} from '../../services/admin'

export default function FreeStreamCheck({eligible}:{eligible:boolean}){
  const [role,setRole]=useState('admin')
  const [language,setLanguage]=useState('English')
  const [output,setOutput]=useState('')
  const [status,setStatus]=useState('')
  const [busy,setBusy]=useState(false)
  const active=useRef<AbortController|null>(null)
  useEffect(()=>()=>active.current?.abort(),[])
  async function run(){
    if(!eligible || active.current) return
    const controller=new AbortController()
    active.current=controller
    setOutput('');setBusy(true);setStatus('Waiting for the provider…')
    const timer=window.setTimeout(()=>controller.abort(),20000)
    try{
      await streamAiBenchmark(role,language,piece=>setOutput(prev=>prev+piece),controller.signal)
      setStatus('Stream complete.')
    }catch(error){
      setOutput('')
      setStatus(controller.signal.aborted?'Stream stopped.':error instanceof Error?error.message:'Stream unavailable.')
    }finally{
      window.clearTimeout(timer)
      active.current=null
      setBusy(false)
    }
  }
  return <details><summary>Test Groq streaming</summary>
    <p>Sends a fixed example about a ₹73 assistance fee. Each check uses one request from the verified free allowance.</p>
    <label>Model role <select aria-label="Model role" value={role} disabled={busy} onChange={e=>setRole(e.target.value)}>
      <option value="client">Client · 20B</option><option value="admin">Admin · 120B</option>
    </select></label>{' '}
    <label>Language <select aria-label="Language" value={language} disabled={busy} onChange={e=>setLanguage(e.target.value)}>
      {['English','Hindi','Telugu'].map(name=><option key={name}>{name}</option>)}
    </select></label>{' '}
    <button type="button" disabled={busy||!eligible} onClick={run}>Run streaming check</button>
    {busy&&<button type="button" onClick={()=>active.current?.abort()}>Stop</button>}
    <p role="status">{eligible?status:'A verified free Groq account is required.'}</p>
    {output&&<p>{output}</p>}
  </details>
}
