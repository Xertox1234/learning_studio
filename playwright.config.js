// Playwright configuration for Python Learning Studio
// Testing JWT cookie authentication migration (PR #15)

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e-tests',

  // Maximum time one test can run
  timeout: 30 * 1000,

  // Maximum time expect() should wait for condition
  expect: {
    timeout: 5000,
  },

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry on CI only
  retries: process.env.CI ? 2 : 0,

  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,

  // Reporter to use
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results/results.json' }]
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL for navigation
    baseURL: 'http://localhost:3000',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Take screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'retain-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    // Test against mobile viewports
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  // Note: Servers should be started manually before running tests
  // Django: DJANGO_SETTINGS_MODULE=learning_community.settings.development venv/bin/python manage.py runserver
  // React: cd frontend && npm run dev

  // Uncomment webServer config only if you want Playwright to auto-start servers
  // webServer: [
  //   {
  //     command: 'DJANGO_SETTINGS_MODULE=learning_community.settings.development venv/bin/python manage.py runserver',
  //     url: 'http://127.0.0.1:8000',
  //     reuseExistingServer: true,
  //     timeout: 120 * 1000,
  //   },
  //   {
  //     command: 'cd frontend && npm run dev',
  //     url: 'http://localhost:3000',
  //     reuseExistingServer: true,
  //     timeout: 120 * 1000,
  //   },
  // ],
});
