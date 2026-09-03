import axios from 'axios'
import { authHeader } from './auth'
import { apiBase } from './apiBase'
import { clearServiceCatalog } from './serviceCatalog'

const api = axios.create({ baseURL: apiBase, timeout: 15000 })

export async function fetchAdminOrders(page=1, per_page=20, status='', q='', date_from='', date_to='', archive='active'){
  const params:any = { page, per_page }
  if(status) params.status = status
  if(q) params.q = q
  if(date_from) params.date_from = date_from
  if(date_to) params.date_to = date_to
  params.archive = archive
  const res = await api.get('/admin/orders', { params, headers: authHeader() })
  return res.data
}
export async function setOrderArchived(orderId:number, archived:boolean){ return (await api.post(`/admin/orders/${orderId}/archive`, {archived}, {headers:authHeader()})).data }
export async function fetchAdminOverview(){ return (await api.get('/admin/overview', { headers: authHeader() })).data }
export async function fetchAdminJobs(filters:Record<string,string|number>={}){ return (await api.get('/admin/jobs',{params:filters,headers:authHeader()})).data }
export async function fetchAdminJobSources(){ return (await api.get('/admin/job-sources',{headers:authHeader()})).data }
export async function updateAdminJob(id:number,payload:any){ return (await api.patch(`/admin/jobs/${id}`,payload,{headers:authHeader()})).data }
export async function synchronizeJobs(){ return (await api.post('/admin/jobs/synchronize',{}, {headers:authHeader(),timeout:90000})).data }
export async function fetchAdminUsers(page=1, q=''){ return (await api.get('/admin/users', { params:{page, per_page:20, q}, headers:authHeader() })).data }
export async function fetchAdminUser(id:number){ return (await api.get(`/admin/users/${id}`, {headers:authHeader()})).data }
export async function setClientActive(id:number, active:boolean){ return (await api.post(`/admin/users/${id}/active`, {active}, {headers:authHeader()})).data }
export async function fetchAdminDocuments(page=1){ return (await api.get('/admin/documents', { params:{page, per_page:20}, headers:authHeader() })).data }
export async function sendClientNotification(payload:any){ return (await api.post('/admin/notifications', payload, { headers:authHeader() })).data }
export async function fetchAdminProfile(){ return (await api.get('/admin/profile', { headers:authHeader() })).data }
export async function updateAdminProfile(payload:any){ return (await api.put('/admin/profile', payload, { headers:authHeader() })).data }
export async function fetchSystemReadiness(){ return (await api.get('/admin/system-readiness', {headers:authHeader()})).data }
export async function fetchDatabaseManifest(){ return (await api.get('/admin/database-manifest', {headers:authHeader()})).data }
export function requestReportUrl(filters:Record<string,string>={}){ const params=new URLSearchParams(Object.entries(filters).filter(([,value])=>value));return `${apiBase}/admin/reports/requests.csv${params.size?`?${params}`:''}` }
export async function fetchReportSummary(filters:Record<string,string>={}){ return (await api.get('/admin/reports/summary',{params:filters,headers:authHeader()})).data }
export async function updateOrderStatus(orderId:number,status:string,note?:string){ return (await api.post(`/admin/orders/${orderId}/status`,{status,note},{headers:authHeader()})).data }
export async function fetchServices(){ const res=await api.get('/admin/services',{headers:authHeader()});return Array.isArray(res.data)?res.data:(res.data.items||[]) }
export async function fetchCategories(){ const res=await api.get('/categories/');return Array.isArray(res.data)?res.data:[] }
export async function createCategory(name:string){ return (await api.post('/categories/',{name},{headers:authHeader()})).data }
export async function createService(payload:any){ const res=await api.post('/services/',payload,{headers:authHeader()});clearServiceCatalog();return res.data }
export async function updateService(id:number,payload:any){ const res=await api.put(`/services/${id}`,payload,{headers:authHeader()});clearServiceCatalog();return res.data }
export async function setServiceActive(id:number,active:boolean){ const res=await api.post(`/services/${id}/active`,{active},{headers:authHeader()});clearServiceCatalog();return res.data }
export async function updateAllAssistanceFees(price_inr:number){ const res=await api.put('/admin/services/assistance-fee',{price_inr,confirm:true},{headers:authHeader()});clearServiceCatalog();return res.data }
export async function fetchHomepageAssistanceFee(){ return (await api.get('/admin/services/homepage-assistance-fee',{headers:authHeader()})).data }
export async function updateHomepageAssistanceFee(price_inr:number){ return (await api.put('/admin/services/homepage-assistance-fee',{price_inr},{headers:authHeader()})).data }
export async function fetchJobAssistanceFee(){ return (await api.get('/fees/job-assistance',{headers:authHeader()})).data }
export async function updateJobAssistanceFee(price_inr:number){ const res=await api.put('/fees/job-assistance',{price_inr},{headers:authHeader()});clearServiceCatalog();return res.data }
export async function fetchScholarshipAssistanceFee(){ return (await api.get('/fees/scholarship-assistance',{headers:authHeader()})).data }
export async function updateScholarshipAssistanceFee(price_inr:number){ const res=await api.put('/fees/scholarship-assistance',{price_inr},{headers:authHeader()});clearServiceCatalog();return res.data }
export async function fetchAdminAudit(page=1){ return (await api.get('/admin/audit',{params:{page,per_page:20},headers:authHeader()})).data }
export async function fetchGrievances(page=1,per_page=20){ return (await api.get('/grievances/admin',{params:{page,per_page},headers:authHeader()})).data }
export async function updateGrievanceStatus(id:number,status:string,response?:string){ return (await api.post(`/grievances/admin/${id}/status`,{status,response},{headers:authHeader()})).data }
export async function fetchReviews(page=1,per_page=20){ return (await api.get('/reviews/admin',{params:{page,per_page},headers:authHeader()})).data }
export async function publishReview(id:number,isPublic=true){ return (await api.post(`/reviews/admin/${id}/publish`,{public:isPublic},{headers:authHeader()})).data }
export async function fetchAdminMessageThreads(){ return (await api.get('/messages/admin',{headers:authHeader()})).data }
export async function fetchAdminMessageThread(userId:number){ return (await api.get(`/messages/admin/${userId}`,{headers:authHeader()})).data }
export async function markAdminMessageThreadRead(userId:number){ return (await api.post(`/messages/admin/${userId}/read`,{},{headers:authHeader()})).data }
export async function sendAdminSupportMessage(userId:number,message:string){ return (await api.post(`/messages/admin/${userId}`,{message},{headers:authHeader()})).data }
