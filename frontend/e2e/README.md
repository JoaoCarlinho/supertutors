# SuperTutors E2E Testing Guide

This directory contains Playwright end-to-end tests for the SuperTutors application. The tests are configured to run in **visible browser mode** so you can witness the tests being executed on your monitor.

## Prerequisites

Before running the tests, ensure you have:

1. **Backend services running**:
   ```bash
   # Terminal 1 - Backend
   cd backend
   source venv/bin/activate
   python run.py
   # Backend runs on http://localhost:5001
   ```

2. **Database and Cache services**:
   - PostgreSQL (port 5432)
   - Redis (port 6379)
   - These are already running in your Docker containers

3. **Ollama LLM service** (if testing AI features):
   ```bash
   ollama serve
   ```

## Installation

Playwright browsers are installed automatically on first run. To manually install:

```bash
npx playwright install
```

## Running Tests

### Quick Start - Visible Browser Mode

```bash
# Run all tests with visible browser (500ms slow-mo)
npm test

# Or use the explicit headed mode
npm run test:headed
```

The browser will open and you'll see the tests running in real-time!

### Alternative Test Modes

```bash
# Interactive UI mode - best for development
npm run test:ui

# Debug mode - step through tests
npm run test:debug

# View last test report
npm run test:report
```

## Test Suites

### 1. Smoke Tests (`smoke.spec.ts`)

Basic functionality and UI element checks:
- Application loads correctly
- Header and branding display
- Connection status indicator
- Chat input area exists
- Message list area exists
- Accessibility features (skip nav)
- Responsive design (mobile/desktop)

```bash
npx playwright test smoke
```

### 2. WebSocket Tests (`websocket.spec.ts`)

Real-time communication tests:
- WebSocket connection establishment
- Connection status updates
- Sending and receiving messages
- Reconnection handling
- Message persistence

```bash
npx playwright test websocket
```

## Configuration

Tests are configured in [`playwright.config.ts`](../playwright.config.ts):

- **Base URL**: `http://localhost:5173`
- **Headless**: `false` (browser visible)
- **Slow Motion**: 500ms (operations slowed for visibility)
- **Screenshots**: Captured on failure
- **Videos**: Recorded on failure
- **Auto-start dev server**: Vite runs automatically

### Adjust Visibility Speed

To change how fast tests run, edit `playwright.config.ts`:

```typescript
use: {
  slowMo: 500,  // Increase for slower, decrease for faster
}
```

### Run in Headless Mode

For CI/CD or faster runs:

```bash
npx playwright test --config=playwright.config.ts --project=chromium --headed=false
```

## Writing New Tests

Create new test files in the `e2e/` directory:

```typescript
import { test, expect } from '@playwright/test';

test.describe('My Feature', () => {
  test('should do something', async ({ page }) => {
    await page.goto('/');
    // Your test code here
  });
});
```

## Debugging Tips

1. **Use UI Mode** for interactive debugging:
   ```bash
   npm run test:ui
   ```

2. **Use Debug Mode** to step through tests:
   ```bash
   npm run test:debug
   ```

3. **Inspect Elements**: Tests pause when browser DevTools are open

4. **View Screenshots/Videos**: Check `test-results/` directory after failures

## Common Issues

### Port Conflicts

If you see "address already in use" errors:
```bash
# Check what's running on port 5173
lsof -i :5173

# Kill the process if needed
kill -9 <PID>
```

### Backend Not Running

Error: "net::ERR_CONNECTION_REFUSED"

Solution: Start the backend first:
```bash
cd backend && source venv/bin/activate && python run.py
```

### WebSocket Connection Failed

Ensure:
1. Backend is running on port 5001
2. `.env` file has correct `VITE_SOCKET_URL=http://localhost:5001`
3. CORS is properly configured in backend

## CI/CD Integration

For automated testing without visible browser:

```bash
CI=1 npm test
```

This will:
- Run in headless mode
- Enable retries (2x)
- Use single worker
- Generate HTML report

## Test Reports

After running tests, view the HTML report:

```bash
npm run test:report
```

This opens an interactive report showing:
- Test results and duration
- Screenshots and videos
- Network activity
- Console logs
- Test steps and timing

## Best Practices

1. **Keep tests independent**: Each test should work in isolation
2. **Use data-testid**: Add `data-testid` attributes for stable selectors
3. **Wait for elements**: Use `await expect().toBeVisible()` instead of hardcoded waits
4. **Clean up**: Close connections and clear data after tests
5. **Mock external APIs**: Don't rely on live external services

## Resources

- [Playwright Documentation](https://playwright.dev)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [API Reference](https://playwright.dev/docs/api/class-playwright)

## Support

For issues or questions:
1. Check the Playwright documentation
2. Review test output and screenshots
3. Use debug mode to step through failing tests
4. Check browser console for runtime errors
