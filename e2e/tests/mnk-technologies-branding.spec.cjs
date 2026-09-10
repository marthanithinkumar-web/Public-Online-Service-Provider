const { test, expect } = require('@playwright/test')

test.describe.configure({ timeout: 120_000 })

test('MNK Technologies product relationship is published consistently', async ({ page }) => {
  for (const route of ['/', '/about', '/privacy', '/terms']) {
    await page.goto(route, { waitUntil: 'domcontentloaded' })
    await expect(page.getByText(/A product of MNK Technologies\./).first()).toBeVisible()
  }

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  const structuredData = await page.locator('#structured-data').textContent()
  expect(structuredData).toContain('MNK Technologies')

  await page.goto('/about', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: 'A product of MNK Technologies', exact: true })).toBeVisible()
  await expect(page.getByText(/Udyam-registered proprietorship/).first()).toBeVisible()

  await page.goto('/terms', { waitUntil: 'domcontentloaded' })
  await expect(page.getByText(/not presented as a private limited or incorporated company/i)).toBeVisible()
})
