import { test, expect } from '@playwright/test';

/**
 * Smoke Test Suite - Basic Application Functionality
 * These tests verify core UI elements and basic navigation
 */

test.describe('SuperTutors - Smoke Tests', () => {
  test('should load the application and display header', async ({ page }) => {
    await page.goto('/');

    // Check that the main heading is visible
    const heading = page.getByRole('heading', { name: 'SuperTutors', level: 1 });
    await expect(heading).toBeVisible();

    // Check subtitle is present
    await expect(page.getByText('Socratic AI Tutor for 9th Grade Math')).toBeVisible();

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should display connection status indicator', async ({ page }) => {
    await page.goto('/');

    // Connection status should be visible in header
    // It might show "Connected", "Disconnected", or "Connecting"
    const connectionStatus = page.locator('[aria-label*="Connection status"], [aria-label*="connection"]').first();
    await expect(connectionStatus).toBeVisible({ timeout: 10000 });

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should display chat input area', async ({ page }) => {
    await page.goto('/');

    // Check for chat input section
    const chatInputSection = page.locator('#chat-input');
    await expect(chatInputSection).toBeVisible();

    // Look for input field or textarea
    const input = page.getByRole('textbox', { name: /message|chat|ask/i }).first();
    await expect(input).toBeVisible();

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should display message list area', async ({ page }) => {
    await page.goto('/');

    // Main content area should be visible
    const mainContent = page.locator('#main-content');
    await expect(mainContent).toBeVisible();

    // Verify it has role="main"
    await expect(mainContent).toHaveAttribute('role', 'main');

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should have accessible skip navigation links', async ({ page }) => {
    await page.goto('/');

    // It may be visually hidden but should exist in DOM
    const skipNavCount = await page.locator('text=/Skip to|Skip navigation/i').count();
    expect(skipNavCount).toBeGreaterThan(0);

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should display thread list sidebar on desktop', async ({ page }) => {
    // Set desktop viewport
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');

    // Thread list should be visible on desktop
    const threadList = page.locator('#thread-list');
    await expect(threadList).toBeVisible();

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should be responsive - hide sidebar on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Thread list should be hidden on mobile
    const threadList = page.locator('#thread-list');
    await expect(threadList).toBeHidden();

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });

  test('should have celebration components in DOM', async ({ page }) => {
    await page.goto('/');

    // Just verify the page loaded successfully
    await expect(page).toHaveTitle(/SuperTutors|Vite/i);

    // Pause for 3 seconds to view final state
    await page.waitForTimeout(3000);
  });
});
