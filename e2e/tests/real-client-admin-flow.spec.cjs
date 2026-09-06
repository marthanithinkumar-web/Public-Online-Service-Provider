const { test, expect } = require('@playwright/test')

const adminEmail = process.env.E2E_ADMIN_EMAIL || 'admin-e2e@example.test'
const adminPassword = process.env.E2E_ADMIN_PASSWORD || 'E2E-Admin-Password-2026!'

function uniqueClient() {
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 100000)}`
  return {
    name: `E2E Client ${suffix}`,
    phone: `9${String(Date.now()).slice(-9)}`,
    email: `client-${suffix}@example.test`,
    password: 'E2E-Client-Password-2026!',
  }
}

test('real client application can be processed to completion by an admin', async ({ browser }) => {
  const client = uniqueClient()
  const clientContext = await browser.newContext()
  const clientPage = await clientContext.newPage()

  await clientPage.goto('/services/residence-certificate')
  await expect(clientPage.getByRole('heading', { name: /Residence Certificate/i }).first()).toBeVisible()
  await clientPage.getByRole('link', { name: 'Create account', exact: true }).click()

  await expect(clientPage).toHaveURL(/\/register\?returnTo=/)
  await clientPage.getByLabel('Name*').fill(client.name)
  await clientPage.getByLabel('Phone number*').fill(client.phone)
  await clientPage.getByLabel('Email address*').fill(client.email)
  await clientPage.getByLabel('Password*', { exact: true }).fill(client.password)
  await clientPage.getByLabel('Confirm password*', { exact: true }).fill(client.password)
  await clientPage.getByRole('button', { name: 'Create account', exact: true }).click()

  await expect(clientPage).toHaveURL(/\/services\/residence-certificate$/)
  await expect(clientPage.getByText(client.name, { exact: true })).toBeVisible()
  await clientPage.getByLabel('Short note').fill('Real browser E2E application submitted for workflow verification.')
  await clientPage.getByRole('button', { name: 'Review request', exact: true }).click()

  await expect(clientPage.getByRole('heading', { name: 'Review before submitting', exact: true })).toBeVisible()
  await clientPage.getByRole('button', { name: 'Submit application', exact: true }).click()
  await expect(clientPage.getByText(/Your reference number is/)).toBeVisible()
  await clientPage.getByRole('link', { name: 'Continue to payment & tracking', exact: true }).click()

  await expect(clientPage).toHaveURL(/\/my-orders\/\d+$/)
  const orderUrl = new URL(clientPage.url())
  const orderId = orderUrl.pathname.split('/').pop()
  expect(orderId).toMatch(/^\d+$/)
  await expect(clientPage.getByRole('heading', { name: 'Application progress', exact: true })).toBeVisible()

  const adminContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  await adminPage.goto('/admin/login')
  await adminPage.getByLabel('Email address').fill(adminEmail)
  await adminPage.getByLabel('Password').fill(adminPassword)
  await adminPage.getByRole('button', { name: 'Sign in securely', exact: true }).click()

  await expect(adminPage).toHaveURL(/\/admin\/dashboard$/)
  await adminPage.goto(`/admin/orders/${orderId}`)
  const adminDetail = adminPage.locator('.admin-order-detail')
  await expect(adminDetail).toContainText(client.name)
  await expect(adminDetail).toContainText('Status: Submitted')

  const statusSelect = adminPage.getByLabel('Next status')
  const note = adminPage.getByLabel('Processing note')
  const updateButton = adminPage.getByRole('button', { name: 'Update request', exact: true })

  await statusSelect.selectOption('Under Review')
  await note.fill('E2E admin started reviewing the application.')
  await updateButton.click()
  await expect(adminDetail).toContainText('Status: Under Review')

  await statusSelect.selectOption('In Progress')
  await note.fill('E2E admin is processing the application.')
  await updateButton.click()
  await expect(adminDetail).toContainText('Status: In Progress')

  await statusSelect.selectOption('Completed')
  await note.fill('E2E request completed by admin.')
  await updateButton.click()
  await expect(adminDetail).toContainText('Status: Completed')
  await expect(adminPage.getByText('This request is closed and can no longer be moved to another status.')).toBeVisible()

  await clientPage.reload()
  await expect(clientPage.locator('.dashboard-hero .status-pill')).toHaveText('Completed')
  await expect(clientPage.getByText('E2E request completed by admin.', { exact: true }).first()).toBeVisible()
  await expect(clientPage.getByText('This application is closed.', { exact: true })).toBeVisible()

  await adminContext.close()
  await clientContext.close()
})
