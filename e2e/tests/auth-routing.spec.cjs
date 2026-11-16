const { test, expect } = require('@playwright/test')

function fakeJwt({ userId = 101, isAdmin = false } = {}) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ user_id: userId, is_admin: isAdmin, exp: Math.floor(Date.now() / 1000) + 3600 })}.e2e`
}

async function installSession(page, { isAdmin = false } = {}) {
  const token = fakeJwt({ isAdmin })
  const user = {
    id: isAdmin ? 1 : 101,
    name: isAdmin ? 'E2E Admin' : 'E2E Client',
    email: isAdmin ? 'admin-e2e@example.test' : 'client-e2e@example.test',
    is_admin: isAdmin,
  }
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('psp_token', token)
    localStorage.setItem('psp_user', JSON.stringify(user))
  }, { token, user })
}

async function mockClientWorkspace(page) {
  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.route('**/api/orders/mine', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
  })
  await page.route('**/api/notifications', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], unread: 0 }) })
  })
  await page.route('**/api/auth/profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ user: { id: 101, name: 'E2E Client', email: 'client-e2e@example.test', is_admin: false } }),
    })
  })
}

test('unauthenticated client workspace redirects to login and preserves destination', async ({ page }) => {
  await page.goto('/my-orders')
  await expect(page).toHaveURL(/\/login\?returnTo=/)
  const current = new URL(page.url())
  expect(current.pathname).toBe('/login')
  expect(current.searchParams.get('returnTo')).toBe('/my-orders')
})

test('unauthenticated admin workspace redirects to admin login', async ({ page }) => {
  await page.goto('/admin/dashboard')
  await expect(page).toHaveURL(/\/admin\/login\?returnTo=/)
  const current = new URL(page.url())
  expect(current.pathname).toBe('/admin/login')
  expect(current.searchParams.get('returnTo')).toBe('/admin/dashboard')
})

test('public service page remains crawlable when the live API lookup fails', async ({ page }) => {
  await page.route('**/api/services/by-slug/pan-card-new-application', async (route) => {
    await route.abort('failed')
  })
  await page.goto('/services/pan-card-new-application')
  await expect(page.getByRole('heading', { name: 'PAN Card - New Application', exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Service unavailable', exact: true })).toHaveCount(0)
})

test('startup-only service remains crawlable when the API is unavailable', async ({ page }) => {
  await page.route('**/api/services/by-slug/residence-certificate', async (route) => {
    await route.abort('failed')
  })
  await page.goto('/services/residence-certificate')
  await expect(page.getByRole('heading', { name: 'Residence Certificate', exact: true })).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Service unavailable', exact: true })).toHaveCount(0)
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', 'https://pospindia.onrender.com/services/residence-certificate')
})

test('client session cannot enter admin routes', async ({ page }) => {
  await installSession(page, { isAdmin: false })
  await mockClientWorkspace(page)
  await page.goto('/admin/dashboard')
  await expect(page).toHaveURL(/\/my-orders$/)
  await expect(page.getByRole('heading', { name: /Welcome, E2E Client/i })).toBeVisible()
})

test('admin session cannot enter client-only routes', async ({ page }) => {
  await installSession(page, { isAdmin: true })
  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.goto('/my-orders')
  await expect(page).toHaveURL(/\/admin\/dashboard$/)
})

test('client session can load its authenticated workspace in Chromium', async ({ page }) => {
  await installSession(page, { isAdmin: false })
  await mockClientWorkspace(page)
  await page.goto('/my-orders')
  await expect(page).toHaveURL(/\/my-orders$/)
  await expect(page.getByRole('heading', { name: /Welcome, E2E Client/i })).toBeVisible()
  await expect(page.getByRole('link', { name: 'Government Services', exact: true })).toBeVisible()

  await page.goto('/my-orders#notifications')
  await expect(page).toHaveURL(/\/my-orders#notifications$/)
  await expect(page.getByRole('heading', { name: 'Notifications', exact: true, level: 1 })).toBeVisible()
  await expect(page.getByText('No notifications.')).toBeVisible()
})

test('primary Services navigation opens the service directory and Track Request preserves the tracking destination', async ({ page }) => {
  await page.goto('/')
  const primary = page.getByRole('navigation', { name: 'Primary navigation' })
  await primary.getByRole('link', { name: 'Services', exact: true }).click()
  await expect(page).toHaveURL(/\/government-services$/)
  await expect(page.getByRole('heading', { name: 'Government Services', level: 1 })).toBeVisible()

  await page.goto('/')
  await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Track Request', exact: true }).click()
  await expect(page).toHaveURL(/\/login\?returnTo=/)
  const current = new URL(page.url())
  expect(current.searchParams.get('returnTo')).toBe('/my-orders#track')
})

test('authenticated desktop and mobile Track Request links open the tracking view instead of the dashboard home', async ({ page }) => {
  await installSession(page, { isAdmin: false })
  await mockClientWorkspace(page)
  await page.goto('/')

  await page.getByRole('navigation', { name: 'Primary navigation' }).getByRole('link', { name: 'Track Request', exact: true }).click()
  await expect(page).toHaveURL(/\/my-orders#track$/)
  await expect(page.getByRole('heading', { name: 'Track My Request', exact: true, level: 1 })).toBeVisible()

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: 'Open navigation menu' }).click()
  await page.getByRole('navigation', { name: 'Mobile navigation' }).getByRole('link', { name: 'Track My Request', exact: true }).click()
  await expect(page).toHaveURL(/\/my-orders#track$/)
  await expect(page.getByRole('heading', { name: 'Track My Request', exact: true, level: 1 })).toBeVisible()
})


test('homepage displays the configured public assistance fee', async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.route('**/api/services/homepage-assistance-fee', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ price_inr: 45 }) })
  })
  await page.goto('/')
  await expect(page.getByText('Homepage assistance fee', { exact: true })).toBeVisible()
  await expect(page.getByText('₹45', { exact: true })).toBeVisible()
})

test('service search cards use the current configured scholarship assistance fee', async ({ page }) => {
  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.route('**/api/services', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([{
        id: 501,
        name: 'National Scholarship Portal (NSP) Assistance',
        category: 'Scholarships & Student Welfare',
        price_inr: 30,
        official_fee_status: 'none',
        official_fee_inr: 0,
        keywords: 'scholarship nsp student',
        is_active: true,
      }]),
    })
  })
  await page.route('**/api/fees/scholarship-assistance', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: { 'Cache-Control': 'no-store' },
      body: JSON.stringify({ price_inr: 85, official_fee_inr: 0, official_fee_status: 'none' }),
    })
  })
  await page.route('**/api/services/homepage-assistance-fee', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ price_inr: 30 }) })
  })
  await page.goto('/')
  await page.getByLabel('Search services').fill('scholarship')
  await expect(page.getByText('Applicable Assistance Fee ₹85', { exact: true })).toBeVisible()
})

test('client login waits for the in-flight Render API warm-up before posting credentials', async ({ page }) => {
  let releaseWarmup
  const warmupGate = new Promise((resolve) => { releaseWarmup = resolve })
  let healthStarted = false
  let healthFinished = false
  let loginRequestedBeforeWarmup = null
  const token = fakeJwt({ userId: 101, isAdmin: false })

  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.route('**/health', async (route) => {
    healthStarted = true
    await warmupGate
    healthFinished = true
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  })
  await page.route('**/api/auth/login', async (route) => {
    loginRequestedBeforeWarmup = !healthFinished
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        token,
        user: { id: 101, name: 'E2E Client', email: 'client-e2e@example.test', is_admin: false },
      }),
    })
  })
  await page.route('**/api/auth/profile', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ user: { id: 101, name: 'E2E Client', email: 'client-e2e@example.test', is_admin: false } }),
    })
  })
  await page.route('**/api/orders/mine', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
  })
  await page.route('**/api/notifications', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], unread: 0 }) })
  })

  await page.goto('/login')
  await expect.poll(() => healthStarted).toBe(true)
  await page.getByLabel('Email Address').fill('client-e2e@example.test')
  await page.getByLabel('Password').fill('test-password')
  await page.getByRole('button', { name: 'Login', exact: true }).click()
  await page.waitForTimeout(100)
  expect(loginRequestedBeforeWarmup).toBe(null)
  releaseWarmup()
  await expect(page).toHaveURL(/my-orders$/)
  expect(loginRequestedBeforeWarmup).toBe(false)
})


test('administrator login also waits for the in-flight Render API warm-up', async ({ page }) => {
  let releaseWarmup
  const warmupGate = new Promise((resolve) => { releaseWarmup = resolve })
  let healthStarted = false
  let healthFinished = false
  let loginRequestedBeforeWarmup = null
  const token = fakeJwt({ userId: 1, isAdmin: true })

  await page.route('**/api/**', async (route) => {
    await route.fulfill({ status: 200, contentType: 'application/json', body: '{}' })
  })
  await page.route('**/health', async (route) => {
    healthStarted = true
    await warmupGate
    healthFinished = true
    await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ status: 'ok' }) })
  })
  await page.route('**/api/auth/login', async (route) => {
    loginRequestedBeforeWarmup = !healthFinished
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        token,
        user: { id: 1, name: 'E2E Admin', email: 'admin-e2e@example.test', is_admin: true },
      }),
    })
  })

  await page.goto('/admin/login')
  await expect.poll(() => healthStarted).toBe(true)
  await page.getByLabel('Email address').fill('admin-e2e@example.test')
  await page.getByLabel('Password').fill('test-password')
  await page.getByRole('button', { name: 'Sign in securely' }).click()
  await page.waitForTimeout(100)
  expect(loginRequestedBeforeWarmup).toBe(null)
  releaseWarmup()
  await expect(page).toHaveURL(/admin\\/dashboard$/)
  expect(loginRequestedBeforeWarmup).toBe(false)
})
