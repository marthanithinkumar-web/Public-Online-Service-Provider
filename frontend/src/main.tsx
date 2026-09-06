import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './styles/global.css'
import './styles/admin-service-search.css'
import './styles/latest-jobs-layout.css'
import { getUser } from './services/localStorage'
import { enableWebPush, syncWebPushIfGranted, webPushSupported } from './services/webPush'

// Requirement fields remain optional unless their existing validation marks them required.
const cleanOptionalCopy=(root:ParentNode=document)=>{
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT);const nodes:Text[]=[]
  while(walker.nextNode())nodes.push(walker.currentNode as Text)
  nodes.forEach(node=>{const parent=node.parentElement;if(!parent||parent.closest('script,style,input,textarea,select,option'))return;const cleaned=(node.nodeValue||'').replace(/\s*\(optional at request stage\)/gi,'').replace(/\s*\(optional\)/gi,'').replace(/\boptional\b/gi,'').replace(/\s{2,}/g,' ');if(cleaned!==node.nodeValue)node.nodeValue=cleaned})
}
const observer=new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(node=>{if(node.nodeType===Node.TEXT_NODE){const text=node as Text;const cleaned=(text.nodeValue||'').replace(/\s*\(optional at request stage\)/gi,'').replace(/\s*\(optional\)/gi,'').replace(/\boptional\b/gi,'').replace(/\s{2,}/g,' ');if(cleaned!==text.nodeValue)text.nodeValue=cleaned}else if(node.nodeType===Node.ELEMENT_NODE)cleanOptionalCopy(node as Element)})))
observer.observe(document.body,{childList:true,subtree:true})

createRoot(document.getElementById('root')!).render(<React.StrictMode><BrowserRouter><Routes><Route path="/*" element={<App />} /></Routes></BrowserRouter></React.StrictMode>)
queueMicrotask(()=>cleanOptionalCopy())

// Browsers require notification permission to follow a user gesture. Offer the same
// zero-cost Web Push opt-in to clients and admins after login. If permission was already
// granted on this device, silently bind the existing browser subscription to the current
// signed-in account so account/session changes do not lose notifications.
const maybeOfferWebPush=async()=>{
  const user=getUser()
  if(!user||!webPushSupported())return
  const userKey=String((user as any).id||(user as any).email||((user as any).is_admin?'admin':'client'))
  if(Notification.permission==='granted'){
    const syncKey=`push-synced:${userKey}`
    if(sessionStorage.getItem(syncKey))return
    try{await syncWebPushIfGranted();sessionStorage.setItem(syncKey,'1')}catch{/* retry on a later pass */}
    return
  }
  if(Notification.permission!=='default'||document.getElementById('web-push-optin'))return
  const isAdmin=Boolean((user as any).is_admin)
  const button=document.createElement('button')
  button.id='web-push-optin'
  button.textContent=isAdmin?'Enable admin phone notifications':'Enable application notifications'
  button.setAttribute('aria-label',button.textContent)
  Object.assign(button.style,{position:'fixed',right:'16px',bottom:isAdmin?'16px':'82px',zIndex:isAdmin?'9999':'68',padding:'12px 16px',borderRadius:'10px',border:'1px solid currentColor',background:'Canvas',color:'CanvasText',boxShadow:'0 4px 16px rgba(0,0,0,.18)',fontWeight:'600',maxWidth:'calc(100vw - 32px)'})
  button.onclick=async()=>{button.disabled=true;button.textContent='Enabling…';try{await enableWebPush();sessionStorage.setItem(`push-synced:${userKey}`,'1');button.remove()}catch(err){button.disabled=false;button.textContent=err instanceof Error?err.message:'Could not enable notifications'}}
  document.body.appendChild(button)
}

window.addEventListener('load',()=>{void maybeOfferWebPush()})
setInterval(()=>{void maybeOfferWebPush()},2000)
