const { test, expect } = require('@playwright/test')

test.describe.configure({ timeout: 180_000 })

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

function pdf(name, text) {
  return {
    name,
    mimeType: 'application/pdf',
    buffer: Buffer.from(`%PDF-1.4\n% E2E validation document\n1 0 obj<</Type/Catalog>>endobj\n% ${text}\n%%EOF\n`),
  }
}

test('real client and admin can complete payment, documents, chat, grievance, and review journeys', async ({ browser }) => {
  const client = uniqueClient()
  const clientContext = await browser.newContext()
  const clientPage = await clientContext.newPage()
  let paymentCaptured = false
  let checkoutPosts = 0
  let releaseCheckout
  const checkoutGate = new Promise((resolve) => { releaseCheckout = resolve })

  await clientPage.addInitScript(() => {
    window.Razorpay = class RazorpayE2E {
      constructor(options) { this.options = options }
      on() {}
      open() {
        window.setTimeout(() => this.options.handler({
          razorpay_payment_id: 'pay_e2e_no_charge',
          razorpay_order_id: this.options.order_id,
          razorpay_signature: 'e2e-signature',
        }), 0)
      }
    }
  })
  await clientPage.route('**/api/payments/orders/*/status', async (route) => {
    const payment = paymentCaptured ? {
      id: 9001,
      purpose: 'assistance_fee',
      amount_inr: 30,
      status: 'captured',
      razorpay_payment_id: 'pay_e2e_no_charge',
      receipt_available: true,
    } : null
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        payment,
        payments: payment ? [payment] : [],
        breakdown: { assistance_fee_inr: 30, official_fee_inr: 80, official_fee_status: 'known', combined_total_inr: 110 },
        paid_components: { assistance_fee: paymentCaptured, official_fee: false },
        fully_paid: false,
        total_payable_inr: 110,
      }),
    })
  })
  await clientPage.route('**/api/payments/orders/*/checkout', async (route) => {
    checkoutPosts += 1
    await checkoutGate
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        key_id: 'rzp_test_e2e',
        razorpay_order_id: 'order_e2e_no_charge',
        amount: 3000,
        currency: 'INR',
        name: 'Public Online Service Provider',
        description: 'E2E no-charge assistance fee checkout',
        prefill: { name: client.name, email: client.email, contact: client.phone },
        purpose: 'assistance_fee',
      }),
    })
  })
  await clientPage.route('**/api/payments/orders/*/verify', async (route) => {
    paymentCaptured = true
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        message: 'Payment captured and confirmed.',
        payment: { id: 9001, purpose: 'assistance_fee', amount_inr: 30, status: 'captured', razorpay_payment_id: 'pay_e2e_no_charge' },
      }),
    })
  })

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
  await clientPage.getByLabel('Applicant name').fill(client.name)
  await clientPage.getByLabel('Short note').fill('Real browser E2E application submitted for complete workflow verification.')
  await clientPage.getByLabel('Upload documents (multiple)').setInputFiles(pdf('client-initial-proof.pdf', 'initial client proof'))
  await clientPage.getByRole('button', { name: 'Review request', exact: true }).click()

  await expect(clientPage.getByRole('heading', { name: 'Review before submitting', exact: true })).toBeVisible()
  let orderPosts = 0
  let releaseOrder
  const orderGate = new Promise((resolve) => { releaseOrder = resolve })
  await clientPage.route('**/api/orders/', async (route) => {
    if (route.request().method() !== 'POST') return route.continue()
    orderPosts += 1
    await orderGate
    await route.continue()
  })
  const submitButton = clientPage.locator('.simplified-request-form .cta-row .btn-primary')
  await submitButton.click()
  await expect.poll(() => orderPosts).toBe(1)
  await expect(submitButton).toBeDisabled()
  await submitButton.evaluate((button) => { button.click(); button.click() })
  expect(orderPosts).toBe(1)
  releaseOrder()
  await expect(clientPage.getByText(/Your reference number is/)).toBeVisible()
  await clientPage.unroute('**/api/orders/')
  await clientPage.getByRole('link', { name: 'Continue to payment & tracking', exact: true }).click()

  await expect(clientPage).toHaveURL(/\/my-orders\/\d+$/)
  const orderUrl = new URL(clientPage.url())
  const orderId = orderUrl.pathname.split('/').pop()
  expect(orderId).toMatch(/^\d+$/)
  await expect(clientPage.getByRole('heading', { name: 'Application progress', exact: true })).toBeVisible()
  await expect(clientPage.locator('.document-list li').filter({ hasText: 'client-initial-proof.pdf' })).toBeVisible()

  const payButton = clientPage.locator('.payment-option-card').filter({ hasText: 'Pay Assistance Fee' }).getByRole('button')
  await payButton.click()
  await expect.poll(() => checkoutPosts).toBe(1)
  await expect(payButton).toBeDisabled()
  await payButton.evaluate((button) => { button.click(); button.click() })
  expect(checkoutPosts).toBe(1)
  releaseCheckout()
  await expect(clientPage.getByText('Payment received successfully. Your receipt is now available.', { exact: true })).toBeVisible()

  await clientPage.getByRole('button', { name: 'Edit / Complete Application Details', exact: true }).first().click()
  await clientPage.getByLabel('Purpose').fill('E2E edited residence-purpose detail')
  await clientPage.getByRole('button', { name: 'Save Changes', exact: true }).click()
  await expect(clientPage.getByText('Application details updated. The admin has been notified automatically.', { exact: true })).toBeVisible()
  await expect(clientPage.locator('.request-summary p').filter({ hasText: 'E2E edited residence-purpose detail' })).toBeVisible()

  const adminContext = await browser.newContext()
  const adminPage = await adminContext.newPage()
  await adminPage.goto('/admin/login')
  await adminPage.getByLabel('Email address').fill(adminEmail)
  await adminPage.locator('input[type="password"][autocomplete="current-password"]').fill(adminPassword)
  await adminPage.getByRole('button', { name: 'Sign in securely', exact: true }).click()

  await expect(adminPage).toHaveURL(/\/admin\/dashboard$/)
  await adminPage.goto(`/admin/orders/${orderId}`)
  const adminDetail = adminPage.locator('.admin-order-detail')
  await expect(adminDetail).toContainText(client.name)
  await expect(adminDetail).toContainText('Status: Submitted')
  await expect(adminDetail).toContainText('E2E edited residence-purpose detail')

  await adminPage.getByLabel('Next status').selectOption('Under Review')
  await adminPage.getByLabel('Processing note').fill('E2E admin started reviewing the application.')
  await adminPage.getByRole('button', { name: 'Update request', exact: true }).click()
  await expect(adminDetail).toContainText('Status: Under Review')

  await adminPage.getByLabel('Next status').selectOption('Documents Required')
  await adminPage.getByLabel('Processing note').fill('Please upload the current address proof for E2E validation.')
  await adminPage.getByRole('button', { name: 'Update request', exact: true }).click()
  await expect(adminDetail).toContainText('Status: Documents Required')

  await clientPage.reload()
  await expect(clientPage.locator('.dashboard-hero .status-pill')).toHaveText('Documents Required')
  await clientPage.locator('.dashboard-section').filter({ has: clientPage.getByRole('heading', { name: 'Application actions', exact: true }) }).getByRole('link', { name: 'Chat with Admin', exact: true }).click()
  await clientPage.getByLabel('Your message').fill('E2E client asks which address proof is acceptable.')
  await clientPage.getByRole('button', { name: 'Send message', exact: true }).click()
  await expect(clientPage.getByText('E2E client asks which address proof is acceptable.', { exact: true })).toBeVisible()

  await adminPage.goto('/admin/messages')
  await adminPage.getByRole('button', { name: new RegExp(client.name) }).click()
  await expect(adminPage.getByText('E2E client asks which address proof is acceptable.', { exact: true })).toBeVisible()
  await adminPage.getByLabel('Reply').fill('E2E admin confirms a recent utility bill is acceptable.')
  await adminPage.getByRole('button', { name: 'Send reply', exact: true }).click()
  await expect(adminPage.getByText('E2E admin confirms a recent utility bill is acceptable.', { exact: true })).toBeVisible()

  await clientPage.goto('/messages')
  await expect(clientPage.getByText('E2E admin confirms a recent utility bill is acceptable.', { exact: true })).toBeVisible()
  await clientPage.goto(orderUrl.pathname)
  await clientPage.getByLabel('Add documents').setInputFiles(pdf('client-address-proof.pdf', 'requested address proof'))
  await clientPage.getByRole('button', { name: 'Upload Documents', exact: true }).click()
  await expect(clientPage.getByText('1 document uploaded successfully.', { exact: true })).toBeVisible()
  await expect(clientPage.locator('.dashboard-hero .status-pill')).toHaveText('Under Review')

  await adminPage.goto(`/admin/orders/${orderId}`)
  await expect(adminDetail).toContainText('Status: Under Review')
  const deliverySection = adminPage.locator('.dashboard-section').filter({ has: adminPage.getByRole('heading', { name: 'Deliver a result document', exact: true }) })
  await deliverySection.locator('input[type="file"]').setInputFiles(pdf('result-document.pdf', 'admin result document'))
  await deliverySection.getByRole('button', { name: 'Deliver document to client', exact: true }).click()
  await expect(deliverySection.getByText('Document delivered to the client successfully.', { exact: true })).toBeVisible()
  await expect(adminDetail.locator('.document-list li').filter({ hasText: 'result-document.pdf' })).toBeVisible()

  await adminPage.getByLabel('Next status').selectOption('In Progress')
  await adminPage.getByLabel('Processing note').fill('E2E admin is completing the verified request.')
  await adminPage.getByRole('button', { name: 'Update request', exact: true }).click()
  await expect(adminDetail).toContainText('Status: In Progress')
  await adminPage.getByLabel('Next status').selectOption('Completed')
  await adminPage.getByLabel('Processing note').fill('E2E request completed and result document delivered.')
  await adminPage.getByRole('button', { name: 'Update request', exact: true }).click()
  await expect(adminDetail).toContainText('Status: Completed')
  await expect(adminPage.getByText('This request is closed and can no longer be moved to another status.')).toBeVisible()
  await expect(adminDetail.locator('.document-list li').filter({ hasText: 'client-initial-proof.pdf' })).toHaveCount(0)
  await expect(adminDetail.locator('.document-list li').filter({ hasText: 'client-address-proof.pdf' })).toHaveCount(0)
  await expect(adminDetail.locator('.document-list li').filter({ hasText: 'result-document.pdf' })).toBeVisible()

  await clientPage.goto(orderUrl.pathname)
  await expect(clientPage.locator('.dashboard-hero .status-pill')).toHaveText('Completed')
  await expect(clientPage.getByText('E2E request completed and result document delivered.', { exact: true }).first()).toBeVisible()
  await expect(clientPage.getByText('This application is closed.', { exact: true })).toBeVisible()
  await expect(clientPage.locator('.document-list li').filter({ hasText: 'client-initial-proof.pdf' })).toHaveCount(0)
  await expect(clientPage.locator('.document-list li').filter({ hasText: 'client-address-proof.pdf' })).toHaveCount(0)
  await expect(clientPage.locator('.document-list li').filter({ hasText: 'result-document.pdf' })).toBeVisible()
  const unreadBefore = await clientPage.locator('.notification-card.unread').count()
  expect(unreadBefore).toBeGreaterThan(0)
  await clientPage.locator('.notification-card.unread').first().getByRole('button', { name: 'Mark read', exact: true }).click()
  await expect.poll(() => clientPage.locator('.notification-card.unread').count()).toBe(unreadBefore - 1)

  const grievanceText = 'E2E client grievance confirms the completed workflow needs a final response.'
  const grievanceResponse = 'E2E admin reviewed the request and confirmed the delivered result.'
  await clientPage.goto(`/submit-grievance?order_id=${orderId}`)
  await clientPage.getByLabel('Describe the issue').fill(grievanceText)
  await clientPage.getByRole('button', { name: 'Submit grievance', exact: true }).click()
  await expect(clientPage.getByText(/Grievance submitted Code: GV-/)).toBeVisible()

  await adminPage.goto('/admin/grievances')
  const grievanceItem = adminPage.locator('.admin-record-list.stacked > li').filter({ hasText: grievanceText })
  await expect(grievanceItem).toBeVisible()
  await grievanceItem.getByLabel('New status').selectOption('Resolved')
  await grievanceItem.getByLabel('Response to client').fill(grievanceResponse)
  await grievanceItem.getByRole('button', { name: 'Send update', exact: true }).click()
  await expect(grievanceItem).toContainText('Status: Resolved')

  await clientPage.goto('/grievances')
  await expect(clientPage.getByText(grievanceText, { exact: true })).toBeVisible()
  await expect(clientPage.locator('.request-summary').filter({ hasText: 'Provider response' }).getByText(grievanceResponse, { exact: true })).toBeVisible()
  await expect(clientPage.getByText('Resolved', { exact: true }).first()).toBeVisible()

  const reviewText = 'E2E review confirms the complete client and administrator journey.'
  await clientPage.goto(`/submit-review?order_id=${orderId}`)
  await clientPage.getByLabel('Rating (1–5)').fill('5')
  await clientPage.getByLabel('Comment').fill(reviewText)
  await clientPage.getByRole('button', { name: 'Submit review', exact: true }).click()
  await expect(clientPage.getByText('Thank you for your feedback.', { exact: true })).toBeVisible()

  await adminPage.goto(`/admin/orders/${orderId}`)
  await expect(adminDetail).toContainText(grievanceText)
  await expect(adminDetail).toContainText(reviewText)
  await expect(adminDetail).toContainText('Rating: 5')

  await adminContext.close()
  await clientContext.close()
})
