import api from './api'
import { authHeader } from './auth'

function decodeBase64Url(value:string){
  const padding='='.repeat((4-value.length%4)%4)
  const raw=atob((value+padding).replace(/-/g,'+').replace(/_/g,'/'))
  return Uint8Array.from([...raw].map(c=>c.charCodeAt(0)))
}

export function webPushSupported(){
  return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window
}

async function ensureSubscription(){
  const keyResponse=await api.get('/push/public-key')
  const publicKey=keyResponse.data?.public_key
  if(!publicKey)throw new Error('Push notifications are not configured yet.')
  const registration=await navigator.serviceWorker.register('/push-sw.js')
  await navigator.serviceWorker.ready
  let subscription=await registration.pushManager.getSubscription()
  if(!subscription)subscription=await registration.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:decodeBase64Url(publicKey)})
  await api.post('/push/subscribe',subscription.toJSON(),{headers:authHeader()})
  return true
}

export async function enableWebPush(){
  if(!webPushSupported())throw new Error('Push notifications are not supported on this browser.')
  const permission=await Notification.requestPermission()
  if(permission!=='granted')throw new Error('Notification permission was not granted.')
  return ensureSubscription()
}

export async function syncWebPushIfGranted(){
  if(!webPushSupported()||Notification.permission!=='granted')return false
  return ensureSubscription()
}

export async function disableWebPush(){
  if(!webPushSupported())return
  const registration=await navigator.serviceWorker.getRegistration('/push-sw.js') || await navigator.serviceWorker.getRegistration()
  const subscription=await registration?.pushManager.getSubscription()
  if(subscription){
    await api.delete('/push/subscribe',{headers:authHeader(),data:{endpoint:subscription.endpoint}})
    await subscription.unsubscribe()
  }
}

// Backwards-compatible aliases for any existing admin UI imports.
export const enableAdminWebPush=enableWebPush
export const disableAdminWebPush=disableWebPush
