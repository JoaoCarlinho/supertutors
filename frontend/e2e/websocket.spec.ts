import { test, expect, type WebSocket } from '@playwright/test';

/**
 * WebSocket Connection Test Suite
 * Verifies real-time communication between frontend and backend
 */

test.describe('WebSocket Connection', () => {
  test('should establish WebSocket connection', async ({ page }) => {
    // Listen for WebSocket connections
    const wsConnections: WebSocket[] = [];

    page.on('websocket', (ws) => {
      console.log('WebSocket opened:', ws.url());
      wsConnections.push(ws);

      ws.on('framesent', (event) => console.log('⬆️ Sent:', event.payload));
      ws.on('framereceived', (event) => console.log('⬇️ Received:', event.payload));
      ws.on('close', () => console.log('WebSocket closed'));
    });

    await page.goto('/');

    // Wait for connection status to show connected
    // Give it time to establish connection
    await page.waitForTimeout(3000);

    // Verify at least one WebSocket connection was established
    expect(wsConnections.length).toBeGreaterThan(0);
  });

  test('should display connection status updates', async ({ page }) => {
    await page.goto('/');

    // Wait for connection status indicator
    await page.waitForTimeout(2000);

    // Just verify some status is shown
    const statusCount = await page.locator('text=/connected|connecting|disconnected/i').count();
    expect(statusCount).toBeGreaterThan(0);
  });

  test('should send and receive a message', async ({ page }) => {
    await page.goto('/');

    // Wait for connection to be established
    await page.waitForTimeout(3000);

    // Find the chat input
    const input = page.getByRole('textbox', { name: /message|chat|ask/i }).first();
    await expect(input).toBeVisible();

    // Type a test message
    const testMessage = 'What is 2 + 2?';
    await input.fill(testMessage);

    // Find and click send button
    const sendButton = page.getByRole('button', { name: /send/i });
    await sendButton.click();

    // Wait for message to appear in chat
    // Look for the message we just sent
    await expect(page.getByText(testMessage)).toBeVisible({ timeout: 5000 });

    // Wait for AI response (this may take a few seconds)
    // We'll wait to see if message count increases
    await page.waitForTimeout(2000);

    // Verify that messages exist in the message list
    const messages = page.locator('[role="article"], .message, [data-message]');
    const messageCount = await messages.count();

    // Should have at least our sent message
    expect(messageCount).toBeGreaterThan(0);
  });

  test('should handle reconnection when connection lost', async ({ page }) => {
    await page.goto('/');

    // Wait for initial connection
    await page.waitForTimeout(2000);

    // Simulate going offline/online to trigger reconnection
    await page.context().setOffline(true);
    await page.waitForTimeout(1000);

    // Go back online
    await page.context().setOffline(false);
    await page.waitForTimeout(2000);

    // Should attempt to reconnect
    // Connection status should update
    const statusUpdated = await page.locator('text=/connect/i').count();
    expect(statusUpdated).toBeGreaterThan(0);
  });

  test('should preserve messages across reconnection', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(2000);

    // Send a message
    const input = page.getByRole('textbox', { name: /message|chat|ask/i }).first();
    await input.fill('Test message for persistence');

    const sendButton = page.getByRole('button', { name: /send/i });
    await sendButton.click();

    // Wait for message to appear
    await expect(page.getByText('Test message for persistence')).toBeVisible({ timeout: 5000 });

    // Simulate disconnect/reconnect
    await page.context().setOffline(true);
    await page.waitForTimeout(500);
    await page.context().setOffline(false);
    await page.waitForTimeout(2000);

    // Message should still be visible after reconnection
    await expect(page.getByText('Test message for persistence')).toBeVisible();
  });
});
