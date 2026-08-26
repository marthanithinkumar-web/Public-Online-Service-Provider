import React from 'react'
import {Link} from 'react-router-dom'

const links=[
  ['/my-orders','Dashboard'],
  ['/my-orders#service-search','Find Services'],
  ['/my-orders#applications','My Applications'],
  ['/my-orders#notifications','Notifications'],
  ['/account-settings','Profile & Security'],
  ['/submit-grievance','Help & Feedback'],
] as const

function WorkspaceLinks(){return <>{links.map(([to,label])=><Link key={to} to={to}>{label}</Link>)}<Link className="workspace-delete-link" to="/account-settings#delete-account">Delete Account</Link></>}

export default function ClientWorkspaceNav(){
  return <>
    <aside className="client-workspace-sidebar" aria-label="Client workspace navigation"><div className="workspace-sidebar-title"><strong>My workspace</strong><small>Requests and account</small></div><nav><WorkspaceLinks/></nav></aside>
    <details className="client-workspace-mobile"><summary>My workspace menu</summary><nav><WorkspaceLinks/></nav></details>
  </>
}
