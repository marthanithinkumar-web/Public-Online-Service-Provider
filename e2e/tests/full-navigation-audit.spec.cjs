const { test, expect } = require('@playwright/test')

test.describe.configure({ timeout: 180_000 })

const adminEmail = process.env.E2E_ADMIN_EMAIL || 'admin-e2e@example.test'
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'E2E-Admin-Password-2026!'

function fakeJwt({ userId = 101, isAdmin = false } = {}) {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ user_id: userId, is_admin: isAdmin, exp: Math.floor(Date.now() / 1000) + 3600 })}.e2e`
}

async function installClientSession(page) {
  const token = fakeJwt({ isAdmin: false })
  const user = { id: 101, name: 'Navigation Client', email: 'navigation-client@example.test', phone: '9000000101', is_admin: false }
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('psp_token', token)
    localStorage.setItem('psp_user', JSON.stringify(user))
  }, { token, user })
}

async function installAdminSession(page) {
  const token = fakeJwt({ userId: 1, isAdmin: true })
  const user = { id: 1, name: 'Navigation Admin', email: adminEmail, is_admin: true }
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('psp_token', token)
    localStorage.setItem('psp_user', JSON.stringify(user))
  }, { token, user })
}

async function mockClientWorkspace(page) {
  await page.route('**/api/orders/mine', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.route('**/api/notifications', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], unread: 0 }) }))
  await page.route('**/api/auth/profile', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ user: { id: 101, name: 'Navigation Client', email: 'navigation-client@example.test', phone: '9000000101', is_admin: false, service_profile: {} } }) }))
  await page.route('**/api/grievances/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [] }) }))
  await page.route('**/api/messages/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], messages: [] }) }))
  await page.route('**/api/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }))
}

async function expectRealPage(page) {
  await expect(page.locator('#main-content')).toBeVisible()
  await expect(page.getByRole('heading', { name: /Page not found/i })).toHaveCount(0)
}

test('public header, search and footer links click through to real destinations', async ({ page }) => {
  await page.goto('/about')
  await page.getByRole('link', { name: 'Search services' }).click()
  await expect(page).toHaveURL(/\/#service-search$/)
  await expect(page.getByRole('searchbox', { name: 'Search services' })).toBeVisible()

  const footerLinks = [
    ['Home', '/'],
    ['Jobs', '/jobs'],
    ['Scholarships', '/scholarships'],
    ['MeeSeva Certificates', '/certificates'],
    ['Government Schemes', '/schemes'],
    ['About POSP', '/about'],
    ['Contact', '/contact'],
    ['Privacy', '/privacy'],
    ['Terms', '/terms'],
    ['Disclaimer', '/disclaimer'],
    ['Admin Portal', '/admin/login'],
  ]

  for (const [name, destination] of footerLinks) {
    await page.goto('/')
    const footer = page.locator('footer')
    await footer.getByRole('link', { name, exact: true }).click()
    const url = new URL(page.url())
    expect(url.pathname, `${name} footer destination`).toBe(destination)
    await expectRealPage(page)
  }
})

test('government, recharge, jobs and scholarship cards open their actual detail/application routes', async ({ page }) => {
  await page.goto('/government-services')
  const governmentCard = page.locator('.directory-card').first()
  await expect(governmentCard).toBeVisible()
  await governmentCard.getByRole('link', { name: /View details & apply/i }).click()
  await expect(page).toHaveURL(/\/services\//)
  await expectRealPage(page)

  await page.goto('/recharge-bills')
  const paymentCard = page.locator('.directory-card').first()
  await expect(paymentCard).toBeVisible()
  await paymentCard.getByRole('link', { name: /^Pay/i }).click()
  await expect(page).toHaveURL(/\/recharge-bills\//)
  await expectRealPage(page)

  await page.goto('/jobs')
  const jobCard = page.locator('.job-card').first()
  await expect(jobCard).toBeVisible()
  await jobCard.getByRole('link', { name: 'View Details & Apply', exact: true }).click()
  await expect(page).toHaveURL(/\/jobs\//)
  await expect(page.getByRole('link', { name: /Apply with assistance/i })).toBeVisible()
  await page.getByRole('link', { name: /Apply with assistance/i }).click()
  await expect(page).toHaveURL(/\/services\/apply-government-job\?job=/)
  await expectRealPage(page)

  await page.goto('/scholarships')
  const scholarshipCard = page.locator('.service-card').first()
  await expect(scholarshipCard).toBeVisible()
  await scholarshipCard.getByRole('link', { name: 'View Details & Apply', exact: true }).click()
  await expect(page).toHaveURL(/\/scholarships\//)
  await page.getByRole('link', { name: 'Apply with Assistance', exact: true }).click()
  await expect(page).toHaveURL(/\/services\/scholarship-application-assistance\?scholarship=/)
  await expectRealPage(page)
})

test('every client workspace navigation item is actually clickable and reaches its intended route', async ({ page }) => {
  await installClientSession(page)
  await mockClientWorkspace(page)

  const destinations = [
    ['Home', '/'],
    ['Dashboard', '/my-orders'],
    ['Government Services', '/government-services'],
    ['Aadhaar Seeding / DBT', '/services/aadhaar-bank-account-seeding-dbt-assistance'],
    ['MeeSeva Certificates', '/certificates'],
    ['Jobs', '/jobs'],
    ['Scholarships', '/scholarships'],
    ['Recharge & Bills', '/recharge-bills'],
    ['My Applications', '/my-orders#applications'],
    ['Track My Request', '/my-orders#track'],
    ['Notifications', '/my-orders#notifications'],
    ['Profile & Security', '/account-settings'],
    ['Help & Grievances', '/grievances'],
    ['Delete Account', '/account-settings#delete-account'],
  ]

  for (const [name, destination] of destinations) {
    await page.goto('/my-orders')
    const sidebar = page.getByRole('complementary', { name: 'Client workspace navigation' })
    await sidebar.getByRole('link', { name, exact: true }).click()
    const url = new URL(page.url())
    expect(`${url.pathname}${url.hash}`, `${name} workspace destination`).toBe(destination)
    await expectRealPage(page)
    if (destination === '/my-orders#track') await expect(page.getByRole('heading', { name: 'Track My Request', level: 1 })).toBeVisible()
    if (destination === '/my-orders#applications') await expect(page.getByRole('heading', { name: 'My Applications', level: 1 })).toBeVisible()
    if (destination === '/account-settings#delete-account') await expect(page.getByRole('heading', { name: 'Delete account', level: 2 })).toBeVisible()
  }
})

test('a signed-in client can deliberately open Admin Login instead of being bounced back to the client dashboard', async ({ page }) => {
  await installClientSession(page)
  await mockClientWorkspace(page)
  await page.goto('/')

  await page.getByRole('link', { name: 'Admin Login', exact: true }).click()
  await expect(page).toHaveURL(/\/admin\/login$/)
  await expect(page.getByRole('heading', { name: 'Admin Login', level: 1 })).toBeVisible()

  await page.goto('/')
  await page.locator('footer').getByRole('link', { name: 'Admin Portal', exact: true }).click()
  await expect(page).toHaveURL(/\/admin\/login$/)
  await expect(page.getByRole('heading', { name: 'Admin Login', level: 1 })).toBeVisible()
})

test('admin sidebar, dashboard actions and mobile admin menu point to working admin destinations', async ({ page }) => {
  await page.goto('/admin/login')
  await page.getByLabel('Email address').fill(adminEmail)
  await page.locator('input[type="password"][autocomplete="current-password"]').fill(adminPassword)
  await page.getByRole('button', { name: 'Sign in securely', exact: true }).click()
  await expect(page).toHaveURL(/\/admin\/dashboard$/)

  const destinations = [
    ['Dashboard', '/admin/dashboard'],
    ['Applications', '/admin/orders'],
    ['Job Feed Management', '/admin/jobs'],
    ['Clients', '/admin/users'],
    ['Services & Fees', '/admin/services'],
    ['Notifications', '/admin/notifications'],
    ['Client Messages', '/admin/messages'],
    ['Grievances', '/admin/grievances'],
    ['Reviews', '/admin/reviews'],
    ['Activity & Reports', '/admin/reports'],
    ['Settings', '/admin/settings'],
  ]

  for (const [name, destination] of destinations) {
    await page.goto('/admin/dashboard')
    const adminNav = page.getByRole('navigation', { name: 'Admin navigation' })
    await adminNav.getByRole('link', { name, exact: true }).click()
    const url = new URL(page.url())
    expect(url.pathname, `${name} admin destination`).toBe(destination)
    await expect(page.getByRole('heading', { name, exact: true, level: 1 })).toBeVisible()
  }

  await page.goto('/admin/dashboard')
  const commandGrid = page.getByRole('region', { name: 'Primary admin actions' }).or(page.locator('.admin-command-grid'))
  await expect(page.locator('.admin-command-grid').getByRole('link', { name: /Recharge & Bill Fees/i })).toHaveAttribute('href', '/admin/services')
  await page.locator('.admin-command-grid').getByRole('link', { name: /Recharge & Bill Fees/i }).click()
  await expect(page).toHaveURL(/\/admin\/services$/)

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/admin/dashboard')
  const mobileMenu = page.locator('details.admin-mobile-menu')
  await mobileMenu.locator('summary').click()
  for (const [name, destination] of destinations) {
    await expect(mobileMenu.getByRole('link', { name, exact: true })).toHaveAttribute('href', destination)
  }
})

test('an already-authenticated admin visiting Admin Login returns to the admin workspace', async ({ page }) => {
  await installAdminSession(page)
  await page.route('**/api/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }))
  await page.goto('/admin/login')
  await expect(page).toHaveURL(/\/admin\/dashboard$/)
})
