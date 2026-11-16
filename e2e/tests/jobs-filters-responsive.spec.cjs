const { test, expect } = require('@playwright/test')

function dateFromToday(offset) {
  const today = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Kolkata', year: 'numeric', month: '2-digit', day: '2-digit',
  }).format(new Date())
  const date = new Date(`${today}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + offset)
  return date.toISOString().slice(0, 10)
}

function makeJobs() {
  const now = Date.now()
  return Array.from({ length: 12 }, (_, index) => {
    const engineering = index < 4
    const checkedAt = new Date(now - 1000).toISOString()
    return {
      id: index + 1,
      slug: `filter-job-${index + 1}`,
      title: engineering ? `Engineering Assistant ${index + 1}` : `Public Service Notice ${index + 1}`,
      organization: `Sample Board ${index + 1}`,
      job_type: index === 3 || index > 7 ? 'private' : 'government',
      location: engineering ? 'Hyderabad, Telangana' : 'Delhi, India',
      qualification: engineering ? 'Engineering degree' : 'Any graduate',
      deadline: dateFromToday(index + 5),
      published_at: new Date(now - index * 60_000).toISOString(),
      last_seen_at: checkedAt,
      official_notice_url: 'https://example.gov.in/notice',
      application_url: 'https://example.gov.in/apply',
      status: 'published',
      verification_status: 'official_source_checked',
      is_featured: index === 0,
      source: {
        key: 'sample',
        name: 'Sample Board',
        last_sync_status: 'success',
        last_successful_sync_at: checkedAt,
        last_sync_completed_at: checkedAt,
      },
    }
  })
}

async function openJobs(page) {
  await page.route('**/data/jobs.json', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ items: makeJobs(), sources: [] }),
  }))
  await page.route('**/api/jobs/**', route => route.fulfill({
    contentType: 'application/json',
    body: JSON.stringify({ items: [], total: 0 }),
  }))
  await page.goto('/jobs')
  await expect(page.getByRole('heading', { name: 'Current published notices' })).toBeVisible()
  await expect(page.locator('.job-card').first()).toBeVisible()
}

test('job filters stay synchronized with the URL, cap search length, and remain responsive', async ({ page }) => {
  await openJobs(page)

  const search = page.getByLabel('Search job notices')
  const location = page.getByLabel('Location')
  const qualification = page.getByLabel('Qualification')
  const typeGroup = page.getByRole('group', { name: 'Filter jobs by type' })
  const sort = page.getByLabel('Sort')

  await expect(search).toHaveAttribute('maxlength', '120')
  await search.fill('Engineering')
  await page.getByRole('button', { name: 'Search jobs' }).click()
  await expect(page.locator('.job-card')).toHaveCount(4)
  await expect(page).toHaveURL(/q=Engineering/)

  await typeGroup.getByRole('button', { name: 'Government' }).click()
  await expect(page.locator('.job-card')).toHaveCount(3)
  await expect(page).toHaveURL(/type=government/)

  await location.fill('Hyderabad')
  await qualification.fill('Engineering')
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await expect(page.locator('.job-card')).toHaveCount(3)
  await expect(page).toHaveURL(/location=Hyderabad/)
  await expect(page).toHaveURL(/qualification=Engineering/)

  await sort.selectOption('newest')
  await expect(page.locator('.job-card h3').first()).toContainText('Engineering Assistant 1')
  await expect(page).toHaveURL(/sort=newest/)

  for (const width of [320, 375, 430, 768]) {
    await page.setViewportSize({ width, height: 900 })
    await expect(page.getByRole('heading', { name: 'Current published notices' })).toBeVisible()
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(overflow, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(1)
  }
})
