const EMAIL_LOCAL_RE = /^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$/
const DOMAIN_LABEL_RE = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/

export function normalizeEmail(value:string){
  return value.trim().toLowerCase()
}

export function isValidEmail(value:string){
  const email=normalizeEmail(value)
  if(!email||email.length>254||email.split('@').length!==2)return false
  const [local,domain]=email.split('@')
  if(!local||local.length>64||local.startsWith('.')||local.endsWith('.')||local.includes('..')||!EMAIL_LOCAL_RE.test(local))return false
  if(!domain||domain.length>253||domain.includes('..'))return false
  const labels=domain.split('.')
  const suffix=labels[labels.length-1]||''
  return labels.length>=2&&labels.every(label=>DOMAIN_LABEL_RE.test(label))&&suffix.length>=2&&/^[A-Za-z]+$/.test(suffix)
}

export function normalizeIndianMobile(value:string){
  const raw=value.trim()
  if(!raw||/[^0-9+()\s.-]/.test(raw)||(raw.match(/\+/g)||[]).length>1||(raw.includes('+')&&!raw.startsWith('+')))return null
  let digits=raw.replace(/\D/g,'')
  if(digits.length===12&&digits.startsWith('91'))digits=digits.slice(2)
  else if(digits.length===11&&digits.startsWith('0'))digits=digits.slice(1)
  if(digits.length!==10||!/^[6-9]/.test(digits))return null
  return `+91${digits}`
}
