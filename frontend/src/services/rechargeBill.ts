import axios from 'axios'
import {apiBase} from './apiBase'

const api=axios.create({baseURL:apiBase,timeout:10000})

export const RECHARGE_BILL_SERVICE_NAME='Recharge & Bill Payments'
export const RECHARGE_BILL_TYPES=[
  {id:'mobile_prepaid',label:'Mobile Recharge'},
  {id:'mobile_postpaid',label:'Mobile Postpaid'},
  {id:'dth',label:'DTH'},
  {id:'fastag',label:'FASTag'},
  {id:'electricity',label:'Electricity'},
  {id:'lpg_gas',label:'LPG / Gas'},
  {id:'water',label:'Water'},
  {id:'broadband_landline',label:'Broadband / Landline'},
] as const

export async function fetchRechargeBillAssistanceFee(){
  const response=await api.get('/fees/recharge-bill-assistance')
  return response.data as {price_inr:number}
}

export function validIndianMobileNumber(value:string){
  return /^[6-9]\d{9}$/.test(value.replace(/\D/g,''))
}
