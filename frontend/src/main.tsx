import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import App from './App'
import './styles/global.css'
import './styles/admin-service-search.css'

// Requirement fields remain optional unless their existing validation marks them required.
// This presentation-only cleanup removes repeated "optional" wording without changing validation.
const cleanOptionalCopy=(root:ParentNode=document)=>{
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT)
  const nodes:Text[]=[]
  while(walker.nextNode())nodes.push(walker.currentNode as Text)
  nodes.forEach(node=>{
    const parent=node.parentElement
    if(!parent||parent.closest('script,style,input,textarea,select,option'))return
    const cleaned=(node.nodeValue||'')
      .replace(/\s*\(optional at request stage\)/gi,'')
      .replace(/\s*\(optional\)/gi,'')
      .replace(/\boptional\b/gi,'')
      .replace(/\s{2,}/g,' ')
    if(cleaned!==node.nodeValue)node.nodeValue=cleaned
  })
}

const observer=new MutationObserver(records=>records.forEach(record=>record.addedNodes.forEach(node=>{
  if(node.nodeType===Node.TEXT_NODE){
    const text=node as Text
    const cleaned=(text.nodeValue||'').replace(/\s*\(optional at request stage\)/gi,'').replace(/\s*\(optional\)/gi,'').replace(/\boptional\b/gi,'').replace(/\s{2,}/g,' ')
    if(cleaned!==text.nodeValue)text.nodeValue=cleaned
  }else if(node.nodeType===Node.ELEMENT_NODE)cleanOptionalCopy(node as Element)
})))
observer.observe(document.body,{childList:true,subtree:true})

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/*" element={<App />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
)

queueMicrotask(()=>cleanOptionalCopy())
