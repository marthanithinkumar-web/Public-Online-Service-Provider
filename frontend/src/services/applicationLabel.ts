export function applicationName(order:any){
  const data=order?.application_data||{}
  const jobTitle=String(data.job_title||'').trim()
  const organization=String(data.job_organization||'').trim()
  if(jobTitle)return organization?`${jobTitle} — ${organization}`:jobTitle
  return String(order?.service||'Application')
}

export function applicationSearchText(order:any){
  return `${order?.order_code||''} ${order?.service||''} ${applicationName(order)}`.toLowerCase()
}
