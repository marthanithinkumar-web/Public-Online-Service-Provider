import axios from 'axios'
import {apiBase} from './apiBase'

const FEE_TIMEOUT_MS=7000

export async function fetchHomepageAssistanceFee(){
  return (await axios.get(`${apiBase}/services/homepage-assistance-fee`,{timeout:FEE_TIMEOUT_MS})).data
}

export async function fetchPublicScholarshipAssistanceFee(){
  return (await axios.get(`${apiBase}/fees/scholarship-assistance`,{timeout:FEE_TIMEOUT_MS})).data
}
