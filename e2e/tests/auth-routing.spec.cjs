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
  await expect(page.getByText('No notifications.')).toBeVisible()
})
