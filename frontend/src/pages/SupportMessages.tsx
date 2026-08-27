import React from 'react'
import ClientWorkspaceNav from '../components/ui/ClientWorkspaceNav'
import ClientSupportChat from '../components/ui/ClientSupportChat'

export default function SupportMessages(){return <div className="client-workspace-shell"><ClientWorkspaceNav/><main className="client-dashboard"><section className="dashboard-hero"><div><span className="eyebrow">Client support</span><h1>Private messages</h1><p>Contact the service team and keep every reply in your account.</p></div></section><ClientSupportChat/></main></div>}
