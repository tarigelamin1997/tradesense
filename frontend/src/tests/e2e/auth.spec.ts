import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should redirect unauthenticated users to login', async ({ page }) => {
    // Try to access protected route
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    await expect(page.locator('h1')).toContainText('Login');
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill login form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123!@#');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Should show user menu
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.goto('/login');
    
    // Fill with invalid credentials
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should show error message
    await expect(page.locator('[role="alert"]')).toContainText('Invalid credentials');
    
    // Should stay on login page
    await expect(page).toHaveURL('/login');
  });

  test('should validate email format', async ({ page }) => {
    await page.goto('/login');
    
    // Enter invalid email
    await page.fill('input[name="email"]', 'notanemail');
    await page.fill('input[name="password"]', 'Test123!@#');
    
    // Try to submit
    await page.click('button[type="submit"]');
    
    // Should show validation error
    await expect(page.locator('input[name="email"]:invalid')).toBeVisible();
  });

  test('should logout successfully', async ({ page, context }) => {
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
    
    await page.goto('/dashboard');
    
    // Click user menu
    await page.click('[data-testid="user-menu"]');
    
    // Click logout
    await page.click('button:has-text("Logout")');
    
    // Should redirect to home
    await expect(page).toHaveURL('/');
    
    // Should not show user menu
    await expect(page.locator('[data-testid="user-menu"]')).not.toBeVisible();
  });

  test('should handle session expiry', async ({ page, context }) => {
    // Mock expired session
    await context.addCookies([{
      name: 'auth-token',
      value: 'expired-token',
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'Lax'
    }]);
    
    // Mock API to return 401
    await page.route('**/api/auth/me', route => {
      route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Unauthorized' })
      });
    });
    
    await page.goto('/dashboard');
    
    // Should redirect to login
    await expect(page).toHaveURL('/login');
    
    // Should show session expired message
    await expect(page.locator('[role="alert"]')).toContainText('Session expired');
  });

  test('should register new account', async ({ page }) => {
    await page.goto('/register');
    
    // Fill registration form
    await page.fill('input[name="name"]', 'New User');
    await page.fill('input[name="email"]', 'newuser@example.com');
    await page.fill('input[name="password"]', 'SecurePass123!@#');
    await page.fill('input[name="confirmPassword"]', 'SecurePass123!@#');
    
    // Accept terms
    await page.check('input[name="acceptTerms"]');
    
    // Submit form
    await page.click('button[type="submit"]');
    
    // Should redirect to onboarding or dashboard
    await expect(page).toHaveURL(/\/(onboarding|dashboard)/);
  });

  test('should validate password strength', async ({ page }) => {
    await page.goto('/register');
    
    // Enter weak password
    await page.fill('input[name="password"]', 'weak');
    
    // Should show password requirements
    await expect(page.locator('[data-testid="password-requirements"]')).toBeVisible();
    await expect(page.locator('[data-testid="password-requirements"]')).toContainText('At least 8 characters');
    await expect(page.locator('[data-testid="password-requirements"]')).toContainText('One uppercase letter');
    await expect(page.locator('[data-testid="password-requirements"]')).toContainText('One number');
    await expect(page.locator('[data-testid="password-requirements"]')).toContainText('One special character');
  });

  test('should handle rate limiting', async ({ page }) => {
    await page.goto('/login');
    
    // Mock rate limit response
    let attempts = 0;
    await page.route('**/api/auth/login', route => {
      attempts++;
      if (attempts > 3) {
        route.fulfill({
          status: 429,
          contentType: 'application/json',
          headers: { 'Retry-After': '60' },
          body: JSON.stringify({ error: 'Rate limit exceeded' })
        });
      } else {
        route.fulfill({
          status: 401,
          contentType: 'application/json',
          body: JSON.stringify({ error: 'Invalid credentials' })
        });
      }
    });
    
    // Try multiple login attempts
    for (let i = 0; i < 4; i++) {
      await page.fill('input[name="email"]', 'test@example.com');
      await page.fill('input[name="password"]', 'wrong');
      await page.click('button[type="submit"]');
      await page.waitForTimeout(100);
    }
    
    // Should show rate limit error
    await expect(page.locator('[role="alert"]')).toContainText('Too many attempts');
  });

  test('should persist login across page refreshes', async ({ page, context }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'Test123!@#');
    
    // Mock successful login
    await page.route('**/api/auth/login', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: {
          'Set-Cookie': 'auth-token=mock-token; Path=/; HttpOnly; SameSite=Lax'
        },
        body: JSON.stringify({
          user: {
            id: '123',
            email: 'test@example.com',
            name: 'Test User',
            role: 'user'
          }
        })
      });
    });
    
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');
    
    // Refresh page
    await page.reload();
    
    // Should still be on dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });
});