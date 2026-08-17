import React from 'react'
import { Link, Routes, Route } from 'react-router-dom'
import AdminDashboard from './AdminDashboard'
import OrderManagement from './OrderManagement'
import ServiceManagement from './ServiceManagement'
import GrievanceManagement from './GrievanceManagement'
import ReviewManagement from './ReviewManagement'
import AdminOrderDetail from './AdminOrderDetail'

export default function AdminPanel(){
  return (
    <div style={{padding:16}}>
      <h1>Admin Panel</h1>
      <nav style={{display:'flex',gap:12,flexWrap:'wrap'}}>
        <Link to="/admin/dashboard">Dashboard</Link>
        <Link to="/admin/orders">Orders</Link>
        <Link to="/admin/services">Services</Link>
        <Link to="/admin/grievances">Grievances</Link>
        <Link to="/admin/reviews">Reviews</Link>
      </nav>

      <div style={{marginTop:18}}>
        <Routes>
          <Route path="/dashboard" element={<AdminDashboard/>} />
          <Route path="/orders" element={<OrderManagement/>} />
          <Route path="/orders/:id" element={<AdminOrderDetail/>} />
          <Route path="/services" element={<ServiceManagement/>} />
          <Route path="/grievances" element={<GrievanceManagement/>} />
          <Route path="/reviews" element={<ReviewManagement/>} />
        </Routes>
      </div>
    </div>
  )
}
