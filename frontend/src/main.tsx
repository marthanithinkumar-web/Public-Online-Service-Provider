import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './styles/global.css'
import './styles/admin-service-search.css'
import './styles/latest-jobs-layout.css'
import { getUser } from './services/localStorage'
import { enableAdminWebPush, webPushSupported } from './services/webPush'

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

// Browsers require notification permission to follow a user gesture. For an admin who
// has not chosen yet, show one small enable button after login instead of prompting on load.
window.addEventListener('load',()=>{
  if(!getUser()?.is_admin||!webPushSupported()||Notification.permission!=='default'||document.getElementById('admin-push-optin'))return
  const button=document.createElement('button');button.id='admin-push-optin';button.textContent='Enable admin phone notifications';button.setAttribute('aria-label','Enable admin phone notifications');Object.assign(button.style,{position:'fixed',right:'16px',bottom:'16px',zIndex:'9999',padding:'12px 16px',borderRadius:'10px',border:'1px solid currentColor',background:'Canvas',color:'CanvasText',boxShadow:'0 4px 16px rgba(0,0,0,.18)',fontWeight:'600'})
  button.onclick=async()=>{button.disabled=true;button.textContent='Enabling…';try{await enableAdminWebPush();button.remove()}catch(err){button.disabled=false;button.textContent=err instanceof Error?err.message:'Could not enable notifications'}}
  document.body.appendChild(button)
})
