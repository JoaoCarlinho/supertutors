import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for SuperTutors E2E tests
 * Configured for visible browser testing (headless: false)
 */
export default defineConfig({
  testDir: './e2e',

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
    ['list']
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL to use in actions like `await page.goto('/')`
    baseURL: 'http://localhost:5173',

    // Collect trace when retrying the failed test
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',
  },

  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // VISIBLE BROWSER - Set to false to show browser during tests
        headless: false,
        // Note: slowMo is set via launchOptions
        launchOptions: {
          slowMo: 500, // Slow down operations by 500ms for visibility
        },
      },
    },

    // Uncomment to test on Firefox
    // {
    //   name: 'firefox',
    //   use: {
    //     ...devices['Desktop Firefox'],
    //     headless: false,
    //     slowMo: 500,
    //   },
    // },

    // Uncomment to test on WebKit (Safari)
    // {
    //   name: 'webkit',
    //   use: {
    //     ...devices['Desktop Safari'],
    //     headless: false,
    //     slowMo: 500,
    //   },
    // },
  ],

  // Run your local dev server before starting the tests
  // NOTE: Set reuseExistingServer to true so we can manually start the dev server
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true, // Always reuse existing server
    timeout: 120 * 1000,
  },
});
