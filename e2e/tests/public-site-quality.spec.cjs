const { test, expect } = require('@playwright/test')

test.describe.configure({ timeout: 120_000 })

const OFFICIAL_ORIGIN = 'https://pospindia.onrender.com'
const BING_MARKER = 'B852AAE6FC323DE1D7238E54524BDBA9'
const RETIRED_ORIGINS = [
  `https://${['public', 'online', 'service', 'provider', 'ui'].join('-')}.onrender.com`,
  `https://${['public', 'online', 'service', 'provider', 'india'].join('-')}.onrender.com`,
  `https://${['posp', 'aphu'].join('-')}.onrender.com`,
]

const publicRoutes = [
  '/',
  '/government-services',
  '/recharge-bills',
  '/jobs',
  '/scholarships',
  '/meeseva',
  '/certificates',
  '/schemes',
  '/about',
  '/contact',
  '/privacy',
  '/terms',
  '/disclaimer',
  '/services/residence-certificate',
  '/login',
  '/register',
  '/request-reset',
  '/admin/login',
]

async function assertAccessiblePageShell(page, route) {
  const response = await page.goto(route, { waitUntil: 'domcontentloaded' })
  expect(response?.status(), `${route} returned an error status`).toBeLessThan(400)
  await expect(page.locator('#main-content')).toBeVisible()
  await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1)
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toHaveAttribute('href', '#main-content')
  await expect(page.getByRole('heading', { name: 'Service unavailable', exact: true })).toHaveCount(0)

  const issues = await page.evaluate(() => {
    const hasName = (element) => Boolean(
      element.getAttribute('aria-label') ||
      element.getAttribute('aria-labelledby') ||
      element.getAttribute('title') ||
      element.textContent?.trim() ||
      element.querySelector('img[alt]')?.getAttribute('alt')?.trim()
    )
    const controls = [...document.querySelectorAll('input:not([type="hidden"]), select, textarea')]
      .filter((element) => !element.labels?.length && !element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby'))
      .map((element) => element.outerHTML.slice(0, 160))
    const buttons = [...document.querySelectorAll('button')].filter((element) => !hasName(element)).length
    const links = [...document.querySelectorAll('a')].filter((element) => !hasName(element)).length
    return {
      buttons,
      controls,
      imagesWithoutAlt: document.querySelectorAll('img:not([alt])').length,
      links,
      overflow: Math.ceil(document.documentElement.scrollWidth - document.documentElement.clientWidth),
    }
  })
  expect(issues, `${route} has unnamed or overflowing content`).toEqual({
    buttons: 0,
    controls: [],
    imagesWithoutAlt: 0,
    links: 0,
    overflow: 0,
  })

  const canonical = route === '/' ? `${OFFICIAL_ORIGIN}/` : `${OFFICIAL_ORIGIN}${route}`
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', canonical)
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute('content', canonical)
  const html = await page.locator('html').evaluate((element) => element.outerHTML)
  for (const retired of RETIRED_ORIGINS) expect(html).not.toContain(retired)
}

test('desktop public and authentication routes have complete accessible page shells', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 })
  for (const route of publicRoutes) await assertAccessiblePageShell(page, route)
})

test('service search, popular search, directory filters, empty states, and reset actions work', async ({ page }) => {
  await page.goto('/')
  const homeSearch = page.getByRole('searchbox', { name: 'Search services' })
  await homeSearch.fill('rEsIdEnCe')
  await expect(page.locator('.service-list')).toBeVisible()
  await expect(page.locator('.service-list').getByRole('link', { name: /Residence/i }).first()).toBeVisible()

  await page.getByRole('button', { name: 'Ration card', exact: true }).click()
  await expect(homeSearch).toHaveValue('Ration card')
  await expect(page.locator('.service-list').getByRole('link', { name: /Ration Card/i }).first()).toBeVisible()

  await homeSearch.fill('no-such-service-e2e-9081726354')
  await expect(page.getByRole('heading', { name: /No services found/i })).toBeVisible()
  await page.getByRole('button', { name: 'Browse all categories' }).click()
  await expect(homeSearch).toHaveValue('')

  await page.goto('/government-services')
  const directorySearch = page.getByRole('textbox', { name: 'Search Government Services' })
  await directorySearch.fill('passport')
  await expect(page.locator('.directory-card').getByRole('heading', { name: /Passport/i }).first()).toBeVisible()
  await directorySearch.fill('')
  await page.getByRole('button', { name: 'Certificates', exact: true }).click()
  await expect(page.locator('.directory-group').getByRole('heading', { name: 'Certificates', exact: true })).toBeVisible()
  await directorySearch.fill('no-such-service-e2e-9081726354')
  await expect(page.getByRole('heading', { name: 'No matching services found', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Show all services', exact: true }).click()
  await expect(directorySearch).toHaveValue('')
  await expect(page.locator('.directory-card').first()).toBeVisible()
})

test('mobile navigation, static SEO files, Bing marker, and official-only URLs remain valid', async ({ page, request }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  for (const route of ['/', '/government-services', '/jobs', '/services/residence-certificate', '/contact']) {
    await page.goto(route, { waitUntil: 'domcontentloaded' })
    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1)
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true)
  }

  const menuButton = page.getByRole('button', { name: 'Open navigation menu' })
  await menuButton.click()
  await expect(menuButton).toHaveAttribute('aria-expanded', 'true')
  await expect(page.getByRole('navigation', { name: 'Mobile navigation' })).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(menuButton).toHaveAttribute('aria-expanded', 'false')
  await expect(page.getByRole('navigation', { name: 'Mobile navigation' })).toHaveCount(0)

  await page.goto('/')
  await expect(page.locator('meta[name="msvalidate.01"]')).toHaveAttribute('content', BING_MARKER)
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', `${OFFICIAL_ORIGIN}/`)
  await expect(page.locator('meta[property="og:url"]')).toHaveAttribute('content', `${OFFICIAL_ORIGIN}/`)
  const structuredData = await page.locator('#structured-data').textContent()
  expect(structuredData).toContain(OFFICIAL_ORIGIN)

  const [robotsResponse, sitemapResponse, catalogResponse] = await Promise.all([
    request.get('/robots.txt'),
    request.get('/sitemap.xml'),
    request.get('/seo-catalog.json'),
  ])
  expect(robotsResponse.ok()).toBe(true)
  expect(sitemapResponse.ok()).toBe(true)
  expect(catalogResponse.ok()).toBe(true)
  const robots = await robotsResponse.text()
  const sitemap = await sitemapResponse.text()
  const catalog = await catalogResponse.json()

  expect(robots).toContain(`Sitemap: ${OFFICIAL_ORIGIN}/sitemap.xml`)
  expect(robots).toContain('Disallow: /admin\n')
  expect(robots).not.toContain('Disallow: /admin/\n')
  expect(catalog.some((service) => service.slug === 'residence-certificate')).toBe(true)

  const locations = [...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((match) => match[1])
  expect(locations.length).toBeGreaterThan(2000)
  expect(new Set(locations).size).toBe(locations.length)
  expect(locations.every((location) => location.startsWith(`${OFFICIAL_ORIGIN}/`))).toBe(true)
  expect(locations).toContain(`${OFFICIAL_ORIGIN}/services/residence-certificate`)

  const officialFiles = `${robots}\n${sitemap}\n${JSON.stringify(catalog)}\n${structuredData}`
  for (const retired of RETIRED_ORIGINS) expect(officialFiles).not.toContain(retired)
})
