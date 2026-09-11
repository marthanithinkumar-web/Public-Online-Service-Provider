const { test, expect } = require('@playwright/test')

function fakeJwt() {
  const encode = (value) => Buffer.from(JSON.stringify(value)).toString('base64url')
  return `${encode({ alg: 'none', typ: 'JWT' })}.${encode({ user_id: 101, is_admin: false, exp: Math.floor(Date.now() / 1000) + 3600 })}.e2e`
}

async function installClientSession(page) {
  const token = fakeJwt()
  const user = { id: 101, name: 'Navigation Client', email: 'navigation-client@example.test', is_admin: false }
  await page.addInitScript(({ token, user }) => {
    localStorage.setItem('psp_token', token)
    localStorage.setItem('psp_user', JSON.stringify(user))
  }, { token, user })
}

async function mockWorkspace(page) {
  await page.route('**/api/orders/mine', route => route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }))
  await page.route('**/api/notifications', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ items: [], unread: 0 }) }))
  await page.route('**/api/auth/profile', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ user: { id: 101, name: 'Navigation Client', email: 'navigation-client@example.test', is_admin: false } }) }))
  await page.route('**/api/**', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }))
}

test('desktop client navigation links point to their intended destinations', async ({ page }) => {
  await installClientSession(page)
  await mockWorkspace(page)
  await page.goto('/my-orders')

  const primary = page.getByRole('navigation', { name: 'Primary navigation' })
  const primaryLinks = [
    ['Home', '/'],
    ['MeeSeva Certificates', '/certificates'],
    ['Jobs', '/jobs'],
    ['Scholarships', '/scholarships'],
    ['Services', '/government-services'],
    ['Track Request', '/my-orders#track'],
    ['Help', '/contact'],
  ]
  for (const [name, href] of primaryLinks) {
    await expect(primary.getByRole('link', { name, exact: true })).toHaveAttribute('href', href)
  }

  await expect(page.getByRole('link', { name: 'Search services' })).toHaveAttribute('href', '/#service-search')
  await expect(page.getByRole('link', { name: 'Dashboard', exact: true }).last()).toHaveAttribute('href', '/my-orders')
  await expect(page.getByRole('link', { name: 'My Account', exact: true })).toHaveAttribute('href', '/account-settings')

  const workspace = page.getByRole('complementary', { name: 'Client workspace navigation' })
  const workspaceLinks = [
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
  for (const [name, href] of workspaceLinks) {
    await expect(workspace.getByRole('link', { name, exact: true })).toHaveAttribute('href', href)
  }
})

test('mobile client navigation uses the same intended destinations', async ({ page }) => {
  await installClientSession(page)
  await mockWorkspace(page)
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.getByRole('button', { name: 'Open navigation menu' }).click()
  const mobile = page.getByRole('navigation', { name: 'Mobile navigation' })
  await expect(mobile.getByRole('link', { name: 'Services', exact: true })).toHaveAttribute('href', '/government-services')
  await expect(mobile.getByRole('link', { name: 'Search Services', exact: true })).toHaveAttribute('href', '/#service-search')
  await expect(mobile.getByRole('link', { name: 'Track My Request', exact: true })).toHaveAttribute('href', '/my-orders#track')
  await expect(mobile.getByRole('link', { name: 'Dashboard', exact: true })).toHaveAttribute('href', '/my-orders')
  await expect(mobile.getByRole('link', { name: 'My Account', exact: true })).toHaveAttribute('href', '/account-settings')
  await expect(mobile.getByRole('link', { name: 'Messages', exact: true })).toHaveAttribute('href', '/messages')
})
