import React,{useState} from 'react'
import {saveFreeProviderOrder} from '../../services/admin'

type Role='client'|'admin'

export default function ProviderOrder({role,order,onSave}:{role:Role;order:string[];onSave:()=>Promise<void>}){
  const [selected,setSelected]=useState(order)
  const [busy,setBusy]=useState(false)
  const [status,setStatus]=useState('')
  function move(index:number){
    const next=[...selected]
    ;[next[index-1],next[index]]=[next[index],next[index-1]]
    setSelected(next)
  }
  async function save(){
    setBusy(true);setStatus('')
    try{
      await saveFreeProviderOrder(role,selected)
      await onSave()
      setStatus('Saved.')
    }catch{setStatus('Could not save the provider order.')}
    finally{setBusy(false)}
  }
  return <fieldset disabled={busy}><legend>{role==='client'?'Client':'Admin'} provider order</legend>
    <ol>{selected.map((name,i)=><li key={name}>{name}{' '}
      <button type="button" disabled={i===0} onClick={()=>move(i)} aria-label={'Move '+name+' earlier'}>Move up</button>{' '}
      <button type="button" onClick={()=>setSelected(selected.filter(item=>item!==name))} aria-label={'Disable '+name}>Disable</button>
    </li>)}</ol>
    {['groq','gemini','cloudflare','openrouter'].filter(name=>!selected.includes(name)).map(name=>
      <button type="button" key={name} onClick={()=>setSelected([...selected,name])}>Add {name}</button>)}
    {selected.length===0&&<p>Local AI only</p>}
    <button type="button" onClick={save}>Save {role} order</button>
    <span role="status">{status}</span>
  </fieldset>
}
