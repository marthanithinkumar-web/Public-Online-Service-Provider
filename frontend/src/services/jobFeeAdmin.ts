import axios from 'axios'
import {apiBase} from './apiBase'
import {authHeader} from './auth'

export async function saveJobFeeRules(jobId:number,factors:any[],rules:any[]){
  return (await axios.put(`${apiBase}/fees/jobs/${jobId}/rules`,{
    factors,
    rules,
    confirm_from_official_notice:true,
  },{headers:authHeader(),timeout:15000})).data
}

export async function clearJobFeeRules(jobId:number){
  return (await axios.delete(`${apiBase}/fees/jobs/${jobId}/rules`,{headers:authHeader(),timeout:15000})).data
}
