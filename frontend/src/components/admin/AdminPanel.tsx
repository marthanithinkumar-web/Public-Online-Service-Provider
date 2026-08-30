import React from 'react'
import {Link,Navigate,Routes,Route,useLocation} from 'react-router-dom'
import AdminDashboard from './AdminDashboard'
import OrderManagement from './OrderManagement'
import ServiceManagement from './ServiceManagement'
import GrievanceManagement from './GrievanceManagement'
import ReviewManagement from './ReviewManagement'
import AdminOrderDetail from './AdminOrderDetail'
import UserManagement from './UserManagement'
import DocumentManagement from './DocumentManagement'
import NotificationManagement from './NotificationManagement'
import ActivityReports from './ActivityReports'
import AdminSettings from './AdminSettings'
import MessageManagement from './MessageManagement'

const links=[
  ['/admin/dashboard','Dashboard'],
  ['/admin/orders','Applications'],
  ['/admin/users','Clients'],
  ['/admin/services','Services & Fees'],
  ['/admin/documents','Documents'],
  ['/admin/notifications','Notifications'],
  ['/admin/messages','Client Messages'],
  ['/admin/grievances','Grievances'],
  ['/admin/reviews','Reviews'],
  ['/admin/reports','Activity & Reports'],
  ['/admin/settings','Settings'],
] as const

function AdminLinks({pathname}:{pathname:string}){return <>{links.map(([path,label])=><Link key={path} className={pathname===path||pathname.startsWith(`${path}/`)?'active':''} to={path}>{label}</Link>)}</>}

export default function AdminPanel(){
  const location=useLocation()
  return <div className="admin-workspace">
    <aside className="admin-sidebar"><div className="admin-sidebar-title"><strong>Administration</strong><small>Authorized provider workspace</small></div><nav aria-label="Admin navigation"><AdminLinks pathname={location.pathname}/></nav><div className="admin-sidebar-notice">Only authorized admins can view client records and documents.</div></aside>
    <details className="admin-mobile-menu"><summary>Administration menu</summary><nav><AdminLinks pathname={location.pathname}/></nav></details>
    <main className="admin-panel">
      <div className="section-header admin-page-heading"><div><h1>Admin Dashboard</h1></div><Link className="btn btn-secondary" to="/">Public site</Link></div>
      <Routes>
        <Route index element={<Navigate to="/admin/dashboard" replace/>}/>
        <Route path="/dashboard" element={<AdminDashboard/>}/>
        <Route path="/orders" element={<OrderManagement/>}/>
        <Route path="/orders/:id" element={<AdminOrderDetail/>}/>
        <Route path="/services" element={<ServiceManagement/>}/>
        <Route path="/grievances" element={<GrievanceManagement/>}/>
        <Route path="/reviews" element={<ReviewManagement/>}/>
        <Route path="/users" element={<UserManagement/>}/>
        <Route path="/documents" element={<DocumentManagement/>}/>
        <Route path="/notifications" element={<NotificationManagement/>}/>
        <Route path="/messages" element={<MessageManagement/>}/>
        <Route path="/reports" element={<ActivityReports/>}/>
        <Route path="/settings" element={<AdminSettings/>}/>
        <Route path="*" element={<Navigate to="/admin/dashboard" replace/>}/>
      </Routes>
    </main>
  </div>
}
