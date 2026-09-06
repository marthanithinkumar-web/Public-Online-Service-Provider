const CACHE_VERSION = 'posp-notifications-v1'

self.addEventListener('install', () => self.skipWaiting())
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()))

self.addEventListener('message', event => {
  const data = event.data || {}
  if (data.type !== 'SHOW_ADMIN_NOTIFICATION') return
  const title = String(data.title || 'Admin notification').slice(0, 160)
  const body = String(data.body || '').slice(0, 700)
  const url = String(data.url || '/admin')
  event.waitUntil(self.registration.showNotification(title, {
    body,
    icon: '/favicon.svg',
    badge: '/favicon.svg',
    tag: data.tag || undefined,
    data: { url }
  }))
})

self.addEventListener('notificationclick', event => {
  event.notification.close()
  const target = (event.notification.data && event.notification.data.url) || '/admin'
  event.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clients => {
    for (const client of clients) {
      if ('focus' in client) {
        client.navigate(target)
        return client.focus()
      }
    }
    return self.clients.openWindow(target)
  }))
})
