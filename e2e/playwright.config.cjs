const { defineConfig } = require('@playwright/test')

module.exports = defineConfig({
  testDir: './tests',
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  workers: 1,
  retries: 1,
  reporter: 'line',
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://127.0.0.1:4173',
    browserName: 'chromium',
    headless: true,
    trace: 'retain-on-failure',
  },
})
