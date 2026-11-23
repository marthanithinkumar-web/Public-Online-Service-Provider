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
    status: 503,
    body: JSON.stringify({ error: 'API unavailable' }),
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

  await typeGroup.getByRole('button', { name: 'Private' }).click()
  await expect(page.locator('.job-card')).toHaveCount(1)
  await typeGroup.getByRole('button', { name: 'All' }).click()
  await expect(page.locator('.job-card')).toHaveCount(4)
  await typeGroup.getByRole('button', { name: 'Government' }).click()

  await location.fill('Hyderabad')
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await expect(page.locator('.job-card')).toHaveCount(3)
  await qualification.fill('Engineering')
  await page.getByRole('button', { name: 'Apply filters' }).click()
  await expect(page.locator('.job-card')).toHaveCount(3)
  await expect(page).toHaveURL(/location=Hyderabad/)
  await expect(page).toHaveURL(/qualification=Engineering/)

  await sort.selectOption('newest')
  await expect(page.locator('.job-card h3').first()).toContainText('Engineering Assistant 1')
  await expect(page).toHaveURL(/sort=newest/)

  for (const width of [320, 375, 430, 768, 1024]) {
    await page.setViewportSize({ width, height: 900 })
    await expect(page.getByRole('heading', { name: 'Current published notices' })).toBeVisible()
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)
    expect(overflow, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(1)
  }
})

test('featured, deadline, empty-result, reset, and pagination controls work', async ({ page }) => {
  await openJobs(page)

  await expect(page).not.toHaveURL(/featured=/)
  await expect(page.getByLabel('Featured only')).not.toBeChecked()
  await page.getByLabel('Featured only').click()
  await expect(page.locator('.job-card')).toHaveCount(1)
  await expect(page).toHaveURL(/featured=true/)
  await page.getByLabel('Featured only').click()
  await expect(page).not.toHaveURL(/featured=/)

  await page.locator('#job-deadline').selectOption('closing_soon')
  await expect(page.locator('.job-card')).toHaveCount(3)
  await expect(page).toHaveURL(/deadline=closing_soon/)

  await page.locator('#job-deadline').selectOption('this_month')
  const todayMonth = dateFromToday(0).slice(0, 7)
  const thisMonthCount = makeJobs().filter(job => job.deadline.slice(0, 7) === todayMonth).length
  await expect(page.locator('.job-card')).toHaveCount(thisMonthCount)

  await page.getByLabel('Search job notices').fill('no matching notice')
  await page.getByRole('button', { name: 'Search jobs' }).click()
  await expect(page.locator('.job-card')).toHaveCount(0)
  await expect(page.getByText('No matching published notices')).toBeVisible()

  await page.getByRole('button', { name: 'Clear filters' }).click()
  await expect(page.locator('.job-card')).toHaveCount(10)
  await expect(page).not.toHaveURL(/(?:q|featured|deadline|type|location|qualification|sort|page)=/)
  await page.getByRole('button', { name: 'Next' }).click()
  await expect(page.locator('.job-card')).toHaveCount(2)
  await expect(page.getByText('Page 2 of 2')).toBeVisible()
  await page.getByRole('button', { name: 'Previous' }).click()
  await expect(page.locator('.job-card')).toHaveCount(10)
})

test('job directory displays a filtered API page before using the snapshot', async ({page}) => {
  const item = makeJobs()[3]
  await page.route('**/api/jobs/**', route => {
    const query = new URL(route.request().url()).searchParams
    const items = query.get('type') === 'private' ? [item] : []
    return route.fulfill({json: {items, total: items.length, count: items.length, page: 1, limit: 10}})
  })
  await page.goto('/jobs?type=private')
  await expect(page.locator('.job-card')).toHaveCount(1)
  await expect(page.locator('.job-card')).toContainText(item.title)
})
