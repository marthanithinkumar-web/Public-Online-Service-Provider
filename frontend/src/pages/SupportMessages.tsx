import React from 'react'
import ClientWorkspaceNav from '../components/ui/ClientWorkspaceNav'
import ClientSupportChat from '../components/ui/ClientSupportChat'

export default function SupportMessages(){return <div className="client-workspace-shell"><ClientWorkspaceNav/><main className="client-dashboard"><section className="dashboard-hero"><div><span className="eyebrow">Private client support</span><h1>Chat with Admin</h1><p>Send a private message to the administrator and keep every reply together in your account.</p></div></section><ClientSupportChat/></main></div>}
