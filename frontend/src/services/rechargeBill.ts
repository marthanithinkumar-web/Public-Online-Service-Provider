import axios from 'axios'
import {apiBase} from './apiBase'

const api=axios.create({baseURL:apiBase,timeout:10000})

export const MOBILE_RECHARGE_SERVICE_NAME='Mobile Recharge'
export const MOBILE_OPERATORS=['Airtel','Jio','Vi','BSNL'] as const

export async function fetchRechargeBillAssistanceFee(){
  const response=await api.get('/fees/recharge-bill-assistance')
  return response.data as {price_inr:number;official_fee_inr:0;official_fee_status:'none'}
}

export function normalizeIndianMobileNumber(value:string){
  return value.replace(/\D/g,'').replace(/^91(?=[6-9]\d{9}$)/,'')
}

export function validIndianMobileNumber(value:string){
  return /^[6-9]\d{9}$/.test(normalizeIndianMobileNumber(value))
}

export type RechargeAnswers={
  mobile_number?:string
  operator?:string
  circle?:string
  plan_reference?:string
  recharge_amount?:string|number
}

export function validateRechargeAnswers(a:RechargeAnswers){
  if(!validIndianMobileNumber(a.mobile_number||''))return 'Enter a valid 10-digit Indian mobile number.'
  if(!MOBILE_OPERATORS.includes(a.operator as typeof MOBILE_OPERATORS[number]))return 'Select Airtel, Jio, Vi or BSNL.'
  if(!(a.circle||'').trim())return 'Select or enter the mobile circle/state.'
  if(!(a.plan_reference||'').trim())return 'Enter the exact recharge plan or plan reference.'
  const amount=Number(a.recharge_amount)
  if(!Number.isFinite(amount)||amount<=0||amount>100000)return 'Enter a valid recharge amount.'
  return ''
}
