import React from 'react'
import { Link, Routes, Route, useLocation } from 'react-router-dom'
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

const links = [
  ['/admin/dashboard', 'Dashboard'],
  ['/admin/orders', 'Requests'],
  ['/admin/services', 'Services'],
  ['/admin/grievances', 'Grievances'],
  ['/admin/reviews', 'Reviews'],
['/admin/users', 'Users'],
  ['/admin/documents', 'Documents'],
  ['/admin/notifications', 'Notifications'],
  ['/admin/reports', 'Reports'],
  ['/admin/settings', 'Settings'],
] as const

export default function AdminPanel(){
  const location = useLocation()

  return (
    <div className="admin-panel">
      <div className="section-header">
        <div>
          <span className="eyebrow">Management workspace</span>
          <h1>Admin Dashboard</h1>
          <p style={{margin:'8px 0 0',color:'var(--muted)'}}>Manage citizen requests, services, grievances and reviews from one place.</p>
        </div>
        <Link className="btn btn-secondary" to="/">View public site</Link>
      </div>

      <nav className="admin-nav" aria-label="Admin navigation">
        {links.map(([path, label]) => (
          <Link key={path} className={location.pathname === path || location.pathname.startsWith(`${path}/`) ? 'active' : ''} to={path}>{label}</Link>
        ))}
      </nav>

      <div style={{marginTop:22}}>
        <Routes>
          <Route path="/dashboard" element={<AdminDashboard/>} />
          <Route path="/orders" element={<OrderManagement/>} />
          <Route path="/orders/:id" element={<AdminOrderDetail/>} />
          <Route path="/services" element={<ServiceManagement/>} />
          <Route path="/grievances" element={<GrievanceManagement/>} />
          <Route path="/reviews" element={<ReviewManagement/>} />
          <Route path="/users" element={<UserManagement/>} />
          <Route path="/documents" element={<DocumentManagement/>} />
          <Route path="/notifications" element={<NotificationManagement/>} />
          <Route path="/reports" element={<ActivityReports/>} />
          <Route path="/settings" element={<AdminSettings/>} />
        </Routes>
      </div>
    </div>
  )
}
