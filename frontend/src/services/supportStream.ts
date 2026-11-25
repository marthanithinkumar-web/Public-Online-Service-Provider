import {apiBase} from './apiBase'
import {authHeader} from './auth'

export async function sendOptInSupport(message:string, onPartial:(text:string)=>void){
  const controller=new AbortController()
  const timer=window.setTimeout(()=>controller.abort(),60000)
  try{
    const response=await fetch(`${apiBase}/messages/mine`,{
      method:'POST',headers:{...authHeader(),Accept:'application/x-ndjson','Content-Type':'application/json'},
      body:JSON.stringify({message,use_ai:true}),signal:controller.signal,
    })
    if(!response.ok) throw new Error('Support request failed.')
    if(!response.headers.get('content-type')?.includes('application/x-ndjson')) return await response.json()
    if(!response.body) throw new Error('Support stream unavailable.')
    const reader=response.body.getReader()
    const decoder=new TextDecoder()
    let pending='', partial=''
    try{
      for(;;){
        const {value,done}=await reader.read()
        if(done) throw new Error('Incomplete support stream.')
        const lines=(pending+decoder.decode(value,{stream:true})).split('\n')
        pending=lines.pop()||''
        for(const line of lines){
          const event=JSON.parse(line)
          if(event.done?.item) return event.done
          if(event.reset) partial=''
          else if(typeof event.text==='string') partial+=event.text
          onPartial(partial)
        }
      }
    }finally{await reader.cancel();reader.releaseLock()}
  }finally{window.clearTimeout(timer)}
}
