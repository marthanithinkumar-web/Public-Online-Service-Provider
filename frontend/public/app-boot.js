document.documentElement.classList.add('js')

;(function () {
  const retryKey = 'posp-app-boot-retry'
  const retryParam = 'app-retry'

  function appMounted() {
    const root = document.getElementById('root')
    return Boolean(root && !root.querySelector('.app-boot-loader'))
  }

  window.addEventListener('load', function () {
    window.setTimeout(function () {
      if (appMounted()) {
        sessionStorage.removeItem(retryKey)
        return
      }

      if (sessionStorage.getItem(retryKey) === '1') {
        return
      }

      sessionStorage.setItem(retryKey, '1')
      const url = new URL(window.location.href)
      url.searchParams.set(retryParam, Date.now().toString())
      window.location.replace(url.toString())
    }, 5000)
  })
})()
