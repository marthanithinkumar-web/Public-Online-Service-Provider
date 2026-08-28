import React,{useEffect,useState} from 'react'
import axios from 'axios'
import {Link,useSearchParams} from 'react-router-dom'
import AuthLayout from '../components/ui/AuthLayout'
import {apiBase} from '../services/apiBase'

export default function VerifyEmail(){
  const [params]=useSearchParams();const token=params.get('token')||''
  const [state,setState]=useState<'working'|'success'|'error'>(token?'working':'error')
  const [message,setMessage]=useState(token?'Verifying your email address…':'This verification link is incomplete.')
  useEffect(()=>{
    if(!token)return
    let active=true
    axios.post(`${apiBase}/auth/verify`,{token},{timeout:15000}).then(response=>{if(active){setState('success');setMessage(response.data.message||'Account verified.')}}).catch(error=>{if(active){setState('error');setMessage(error?.response?.data?.error||'This verification link is invalid or expired.')}})
    return()=>{active=false}
  },[token])
  return <AuthLayout title="Verify Email" eyebrow="Secure account activation"><div className="auth-card auth-card-modern"><div className="auth-intro"><h2>{state==='success'?'Email verified':'Email verification'}</h2><p className={state==='error'?'info':'success-message'} role="status">{message}</p></div>{state==='success'?<Link className="btn btn-primary btn-block" to="/login">Continue to client login</Link>:state==='error'?<Link className="btn btn-secondary btn-block" to="/request-verification">Request a new link</Link>:null}</div></AuthLayout>
}
