import React from 'react'
import {Link} from 'react-router-dom'

const links=[
  ['/','Home'],
  ['/my-orders','Dashboard'],
  ['/government-services','Government Services'],
  ['/government-services?q=Aadhaar%20Seeding','Aadhaar Seeding / DBT'],
  ['/certificates','MeeSeva Certificates'],
  ['/jobs','Jobs'],
  ['/scholarships','Scholarships'],
  ['/recharge-bills','Recharge & Bills'],
  ['/my-orders#applications','My Applications'],
  ['/my-orders#track','Track My Request'],
  ['/my-orders#notifications','Notifications'],
  ['/account-settings','Profile & Security'],
  ['/grievances','Help & Grievances'],
] as const

function WorkspaceLinks(){return <>{links.map(([to,label])=><Link key={to} to={to}>{label}</Link>)}<Link className="workspace-delete-link" to="/account-settings#delete-account">Delete Account</Link></>}

export default function ClientWorkspaceNav(){
  return <>
    <aside className="client-workspace-sidebar" aria-label="Client workspace navigation"><div className="workspace-sidebar-title"><strong>My workspace</strong><small>Services, opportunities & requests</small></div><nav><WorkspaceLinks/></nav></aside>
    <details className="client-workspace-mobile"><summary>My workspace menu</summary><nav><WorkspaceLinks/></nav></details>
  </>
}
