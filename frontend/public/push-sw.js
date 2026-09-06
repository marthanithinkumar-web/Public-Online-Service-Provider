self.addEventListener('push', event => {
  let data = {}
  try { data = event.data ? event.data.json() : {} } catch (_) {}
  const title = data.title || 'Admin notification'
  const options = {
    body: data.body || 'There is new activity on your website.',
    icon: '/favicon.ico',
    badge: '/favicon.ico',
    data: { url: data.url || '/admin' },
    tag: 'admin-activity',
    renotify: true,
  }
  event.waitUntil(self.registration.showNotification(title, options))
})

self.addEventListener('notificationclick', event => {
  event.notification.close()
  const target = event.notification.data?.url || '/admin'
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windows => {
    for (const client of windows) {
      if ('focus' in client) {
        client.navigate(target)
        return client.focus()
      }
    }
    return clients.openWindow(target)
  }))
})
