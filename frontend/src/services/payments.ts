import axios from 'axios'
import {apiBase} from './apiBase'
import {authHeader} from './auth'

let checkoutPromise:Promise<void>|null=null

function loadCheckout(){
  if((window as any).Razorpay)return Promise.resolve()
  if(checkoutPromise)return checkoutPromise
  checkoutPromise=new Promise((resolve,reject)=>{
    const existing=document.querySelector('script[data-razorpay-checkout]') as HTMLScriptElement|null
    if(existing){existing.addEventListener('load',()=>resolve(),{once:true});existing.addEventListener('error',()=>reject(new Error('Unable to load Razorpay Checkout.')),{once:true});return}
    const script=document.createElement('script')
    script.src='https://checkout.razorpay.com/v1/checkout.js'
    script.async=true
    script.dataset.razorpayCheckout='true'
    script.onload=()=>resolve()
    script.onerror=()=>reject(new Error('Unable to load Razorpay Checkout.'))
    document.head.appendChild(script)
  })
  return checkoutPromise
}

export async function getPaymentStatus(orderId:number){
  return (await axios.get(`${apiBase}/payments/orders/${orderId}/status`,{headers:authHeader(),timeout:15000})).data
}

export async function openPaymentReceipt(orderId:number){
  const response=await axios.get(`${apiBase}/payments/orders/${orderId}/receipt`,{headers:authHeader(),responseType:'blob',timeout:15000})
  const url=URL.createObjectURL(new Blob([response.data],{type:'text/html'}))
  const opened=window.open(url,'_blank','noopener,noreferrer')
  window.setTimeout(()=>URL.revokeObjectURL(url),60000)
  if(!opened)throw new Error('Please allow pop-ups to open the payment receipt.')
}

export async function payRequestTotal(order:any){
  const response=await axios.post(`${apiBase}/payments/orders/${order.id}/checkout`,{}, {headers:authHeader(),timeout:15000})
  if(response.data?.payment?.status==='captured')return response.data.payment
  if(!response.data?.razorpay_order_id)return response.data?.payment||null
  await loadCheckout()
  const data=response.data
  return await new Promise((resolve,reject)=>{
    const Razorpay=(window as any).Razorpay
    const instance=new Razorpay({
      key:data.key_id,amount:data.amount,currency:data.currency,order_id:data.razorpay_order_id,name:data.name,description:data.description,prefill:data.prefill,
      modal:{ondismiss:()=>reject(new Error('Payment window closed.'))},
      handler:async(result:any)=>{
        try{const verified=await axios.post(`${apiBase}/payments/orders/${order.id}/verify`,result,{headers:authHeader(),timeout:15000});resolve(verified.data.payment)}
        catch(error:any){reject(new Error(error?.response?.data?.error||'Payment verification failed.'))}
      },
    })
    instance.on('payment.failed',(result:any)=>reject(new Error(result?.error?.description||'Payment failed. Please try again.')))
    instance.open()
  })
}
