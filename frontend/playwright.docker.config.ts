import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for Docker environment
 * Assumes Docker services are already running via docker-compose
 *
 * Usage: npx playwright test --config=playwright.docker.config.ts
 */
export default defineConfig({
  testDir: './e2e',

  // Run tests in files in parallel
  fullyParallel: true,

  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,

  // Retry failures in Docker (network can be flaky)
  retries: 2,

  // Use fewer workers in Docker to avoid resource issues
  workers: 2,

  // Reporter to use
  reporter: [
    ['html'],
    ['list']
  ],

  // Shared settings for all the projects below
  use: {
    // Base URL for Docker setup
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
        // Headless for Docker
        headless: true,
      },
    },
  ],

  // NO webServer - Docker Compose manages this
  // Ensure docker-compose up is running before tests
});
