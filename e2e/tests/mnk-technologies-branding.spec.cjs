const { test, expect } = require('@playwright/test')

test.describe.configure({ timeout: 120_000 })

test('public POSP pages do not expose MNK Technologies branding or links', async ({ page }) => {
  for (const route of ['/', '/about', '/privacy', '/terms']) {
    await page.goto(route, { waitUntil: 'domcontentloaded' })
    await expect(page.getByText(/MNK Technologies/i)).toHaveCount(0)
    await expect(page.locator('a[href*="mnktechindia.onrender.com"], a[href*="mnktech.onrender.com"]')).toHaveCount(0)
  }

  await page.goto('/', { waitUntil: 'domcontentloaded' })
  const structuredData = await page.locator('#structured-data').textContent().catch(() => '')
  expect(structuredData || '').not.toMatch(/MNK Technologies/i)
})
