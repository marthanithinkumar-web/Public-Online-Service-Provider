const { test, expect } = require('@playwright/test')

test('mobile navigation from a lower-page link starts at the new page heading', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  const about = page.getByRole('contentinfo').getByRole('link', { name: 'About', exact: true })
  await about.scrollIntoViewIfNeeded()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBeGreaterThan(300)
  await about.click()
  await expect(page).toHaveURL(/\/about$/)
  await expect(page.getByRole('heading', { level: 1 })).toBeInViewport()
  await expect.poll(() => page.evaluate(() => window.scrollY)).toBe(0)
})

