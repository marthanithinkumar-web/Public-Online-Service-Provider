import axios from 'axios'
import { authHeader } from './auth'
import { apiBase } from './apiBase'

const api = axios.create({ baseURL: apiBase })

export async function fetchAdminOrders(page=1, per_page=20, status=''){
  const params:any = { page, per_page }
  if(status) params.status = status
  const res = await api.get('/admin/orders', { params, headers: authHeader() })
  return res.data
}

export async function updateOrderStatus(orderId:number, status:string, note?:string){
  const res = await api.post(`/admin/orders/${orderId}/status`, { status, note }, { headers: authHeader() })
  return res.data
}

export async function fetchServices(){
  const res = await api.get('/services')
  return res.data
}

export async function createService(payload:any){
  const res = await api.post('/services', payload, { headers: authHeader() })
  return res.data
}

export async function updateService(id:number, payload:any){
  const res = await api.put(`/services/${id}`, payload, { headers: authHeader() })
  return res.data
}

export async function setServiceActive(id:number, active:boolean){
  const res = await api.post(`/services/${id}/active`, { active }, { headers: authHeader() })
  return res.data
}

export async function fetchGrievances(page=1, per_page=20){
  const res = await api.get('/grievances/admin', { params:{page, per_page}, headers: authHeader() })
  return res.data
}

export async function updateGrievanceStatus(id:number, status:string){
  const res = await api.post(`/grievances/admin/${id}/status`, { status }, { headers: authHeader() })
  return res.data
}

export async function fetchReviews(page=1, per_page=20){
  const res = await api.get('/reviews/admin', { params:{page, per_page}, headers: authHeader() })
  return res.data
}

export async function publishReview(id:number, isPublic=true){
  const res = await api.post(`/reviews/admin/${id}/publish`, { public: isPublic }, { headers: authHeader() })
  return res.data
}
