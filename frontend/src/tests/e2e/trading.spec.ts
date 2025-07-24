import { test, expect } from '@playwright/test';

test.describe('Trading Flow', () => {
  // Setup authenticated state
  test.beforeEach(async ({ page, context }) => {
    // Mock authentication
    await context.addCookies([{
      name: 'auth-token',
      value: 'mock-token',
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'Lax'
    }]);

    // Mock user API response
    await page.route('**/api/auth/me', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          user: {
            id: '123',
            email: 'test@example.com',
            name: 'Test User',
            role: 'user',
            subscription: 'pro'
          }
        })
      });
    });
  });

  test('should display trades list', async ({ page }) => {
    // Mock trades API
    await page.route('**/api/trades*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [
            {
              id: '1',
              symbol: 'AAPL',
              type: 'buy',
              quantity: 100,
              price: 150.50,
              total: 15050,
              executedAt: new Date().toISOString(),
              status: 'completed'
            },
            {
              id: '2',
              symbol: 'GOOGL',
              type: 'sell',
              quantity: 50,
              price: 2800.00,
              total: 140000,
              executedAt: new Date().toISOString(),
              status: 'completed'
            }
          ],
          page: 1,
          pageSize: 10,
          total: 2
        })
      });
    });

    await page.goto('/trades');

    // Should display trades
    await expect(page.locator('[data-testid="trade-card"]')).toHaveCount(2);
    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=GOOGL')).toBeVisible();
  });

  test('should create new trade', async ({ page }) => {
    let tradeCreated = false;

    // Mock trades API
    await page.route('**/api/trades', route => {
      if (route.request().method() === 'POST') {
        const postData = route.request().postDataJSON();
        expect(postData).toEqual({
          symbol: 'AAPL',
          type: 'buy',
          quantity: 100,
          price: 150
        });
        tradeCreated = true;
        route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '3',
            ...postData,
            total: 15000,
            executedAt: new Date().toISOString(),
            status: 'completed'
          })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [], page: 1, pageSize: 10, total: 0 })
        });
      }
    });

    await page.goto('/trades');

    // Click add trade button
    await page.click('[data-testid="add-trade-button"]');

    // Fill trade form
    await page.fill('input[name="symbol"]', 'AAPL');
    await page.selectOption('select[name="type"]', 'buy');
    await page.fill('input[name="quantity"]', '100');
    await page.fill('input[name="price"]', '150');

    // Submit form
    await page.click('button[type="submit"]');

    // Verify trade was created
    expect(tradeCreated).toBe(true);

    // Should show success message
    await expect(page.locator('[role="alert"].success')).toContainText('Trade created successfully');
  });

  test('should validate trade input', async ({ page }) => {
    await page.goto('/trades');
    await page.click('[data-testid="add-trade-button"]');

    // Try to submit empty form
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('input[name="symbol"]:invalid')).toBeVisible();
    await expect(page.locator('input[name="quantity"]:invalid')).toBeVisible();
    await expect(page.locator('input[name="price"]:invalid')).toBeVisible();

    // Enter invalid values
    await page.fill('input[name="symbol"]', 'VERYLONGSYMBOL');
    await page.fill('input[name="quantity"]', '-10');
    await page.fill('input[name="price"]', '0');

    await page.click('button[type="submit"]');

    // Should show specific validation errors
    await expect(page.locator('text=Symbol must be 1-10 characters')).toBeVisible();
    await expect(page.locator('text=Quantity must be positive')).toBeVisible();
    await expect(page.locator('text=Price must be positive')).toBeVisible();
  });

  test('should search trades', async ({ page }) => {
    // Mock search API
    await page.route('**/api/trades*', route => {
      const url = new URL(route.request().url());
      const search = url.searchParams.get('search');
      
      if (search === 'AAPL') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [{
              id: '1',
              symbol: 'AAPL',
              type: 'buy',
              quantity: 100,
              price: 150.50,
              total: 15050,
              executedAt: new Date().toISOString(),
              status: 'completed'
            }],
            page: 1,
            pageSize: 10,
            total: 1
          })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [], page: 1, pageSize: 10, total: 0 })
        });
      }
    });

    await page.goto('/trades');

    // Search for AAPL
    await page.fill('input[placeholder="Search trades..."]', 'AAPL');
    
    // Wait for debounce
    await page.waitForTimeout(350);

    // Should show only AAPL trades
    await expect(page.locator('[data-testid="trade-card"]')).toHaveCount(1);
    await expect(page.locator('text=AAPL')).toBeVisible();
  });

  test('should delete trade', async ({ page }) => {
    let tradeDeleted = false;

    // Mock trades API
    await page.route('**/api/trades*', route => {
      if (route.request().method() === 'DELETE') {
        tradeDeleted = true;
        route.fulfill({ status: 204 });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [{
              id: '1',
              symbol: 'AAPL',
              type: 'buy',
              quantity: 100,
              price: 150.50,
              total: 15050,
              executedAt: new Date().toISOString(),
              status: 'completed'
            }],
            page: 1,
            pageSize: 10,
            total: 1
          })
        });
      }
    });

    await page.goto('/trades');

    // Click delete button on trade
    await page.click('[data-testid="trade-card"] button[aria-label="Delete trade"]');

    // Confirm deletion
    await page.click('button:has-text("Confirm")');

    // Verify trade was deleted
    expect(tradeDeleted).toBe(true);

    // Should show success message
    await expect(page.locator('[role="alert"].success')).toContainText('Trade deleted successfully');
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API error
    await page.route('**/api/trades', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Internal server error' })
      });
    });

    await page.goto('/trades');

    // Should show error message
    await expect(page.locator('[role="alert"].error')).toContainText('Failed to load trades');

    // Should show retry button
    await expect(page.locator('button:has-text("Retry")')).toBeVisible();
  });

  test('should export trades', async ({ page, download }) => {
    // Mock trades API
    await page.route('**/api/trades*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          data: [{
            id: '1',
            symbol: 'AAPL',
            type: 'buy',
            quantity: 100,
            price: 150.50,
            total: 15050,
            executedAt: new Date().toISOString(),
            status: 'completed'
          }],
          page: 1,
          pageSize: 10,
          total: 1
        })
      });
    });

    await page.goto('/trades');

    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="export-trades-button"]');
    
    // Select CSV format
    await page.click('button:has-text("Export as CSV")');

    const downloadEvent = await downloadPromise;
    expect(downloadEvent.suggestedFilename()).toContain('trades');
    expect(downloadEvent.suggestedFilename()).toContain('.csv');
  });

  test('should show trade details', async ({ page }) => {
    // Mock trades API
    await page.route('**/api/trades*', route => {
      const url = new URL(route.request().url());
      if (url.pathname.endsWith('/1')) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '1',
            symbol: 'AAPL',
            type: 'buy',
            quantity: 100,
            price: 150.50,
            total: 15050,
            executedAt: new Date().toISOString(),
            status: 'completed',
            notes: 'Long term investment',
            fees: 10,
            profitLoss: 500
          })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [{
              id: '1',
              symbol: 'AAPL',
              type: 'buy',
              quantity: 100,
              price: 150.50,
              total: 15050,
              executedAt: new Date().toISOString(),
              status: 'completed'
            }],
            page: 1,
            pageSize: 10,
            total: 1
          })
        });
      }
    });

    await page.goto('/trades');

    // Click on trade to view details
    await page.click('[data-testid="trade-card"]');

    // Should show trade details
    await expect(page.locator('h1:has-text("Trade Details")')).toBeVisible();
    await expect(page.locator('text=AAPL')).toBeVisible();
    await expect(page.locator('text=Long term investment')).toBeVisible();
    await expect(page.locator('text=Profit/Loss: $500')).toBeVisible();
  });

  test('should filter trades by date range', async ({ page }) => {
    // Mock filtered API response
    await page.route('**/api/trades*', route => {
      const url = new URL(route.request().url());
      const startDate = url.searchParams.get('startDate');
      const endDate = url.searchParams.get('endDate');

      if (startDate && endDate) {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [{
              id: '1',
              symbol: 'AAPL',
              type: 'buy',
              quantity: 100,
              price: 150.50,
              total: 15050,
              executedAt: '2024-01-15T10:00:00Z',
              status: 'completed'
            }],
            page: 1,
            pageSize: 10,
            total: 1
          })
        });
      } else {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ data: [], page: 1, pageSize: 10, total: 0 })
        });
      }
    });

    await page.goto('/trades');

    // Open date filter
    await page.click('[data-testid="filter-button"]');

    // Set date range
    await page.fill('input[name="startDate"]', '2024-01-01');
    await page.fill('input[name="endDate"]', '2024-01-31');

    // Apply filter
    await page.click('button:has-text("Apply")');

    // Should show filtered results
    await expect(page.locator('[data-testid="trade-card"]')).toHaveCount(1);
    await expect(page.locator('text=Jan 15, 2024')).toBeVisible();
  });
});