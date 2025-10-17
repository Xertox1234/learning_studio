/**
 * E2E Tests for JWT Cookie Authentication - Login Flow
 * Testing PR #15: Migration from localStorage to httpOnly cookies
 */

import { test, expect } from '@playwright/test';
import {
  login,
  verifyJWTCookiesSet,
  verifyTokensNotInJavaScript,
  getCookies,
} from './helpers/auth.js';

test.describe('JWT Cookie Authentication - Login Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear all cookies and localStorage before each test
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should successfully login with valid credentials', async ({ page }) => {
    // Navigate to login page with networkidle to ensure fully loaded
    await page.goto('/login', { waitUntil: 'networkidle' });
    await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible' });

    // Fill in credentials
    await page.fill('input[name="email"], input[type="email"]', 'test@pythonlearning.studio');
    await page.fill('input[name="password"], input[type="password"]', 'testpass123');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await page.waitForURL('**/dashboard', { timeout: 10000 });

    // Verify we're on the dashboard
    expect(page.url()).toContain('/dashboard');
  });

  test('should set httpOnly cookies on successful login', async ({ page }) => {
    await login(page);

    // Verify JWT cookies are set with correct flags
    const { accessToken, refreshToken } = await verifyJWTCookiesSet(page, expect);

    // Verify cookie values are not empty
    expect(accessToken.value).toBeTruthy();
    expect(accessToken.value.length).toBeGreaterThan(20);
    expect(refreshToken.value).toBeTruthy();
    expect(refreshToken.value.length).toBeGreaterThan(20);
  });

  test('should set correct cookie security flags', async ({ page }) => {
    await login(page);

    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    const refreshToken = cookies.find(c => c.name === 'refresh_token');

    // Verify httpOnly flag (prevents JavaScript access)
    expect(accessToken.httpOnly).toBe(true);
    expect(refreshToken.httpOnly).toBe(true);

    // Verify SameSite attribute (CSRF protection)
    expect(accessToken.sameSite).toBe('Lax');
    expect(refreshToken.sameSite).toBe('Lax');

    // Note: Secure flag only set in production (HTTPS)
    // In development (HTTP), secure will be false
    // This is expected and correct behavior
  });

  test('should NOT expose tokens in JavaScript', async ({ page }) => {
    await login(page);

    // Verify tokens are not accessible from document.cookie
    await verifyTokensNotInJavaScript(page, expect);
  });

  test('should NOT store tokens in localStorage', async ({ page }) => {
    await login(page);

    // Check localStorage is empty of tokens
    const localStorageContent = await page.evaluate(() => {
      const items = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        items[key] = localStorage.getItem(key);
      }
      return items;
    });

    // Verify no token-related keys in localStorage
    expect(localStorageContent.authToken).toBeUndefined();
    expect(localStorageContent.access_token).toBeUndefined();
    expect(localStorageContent.refresh_token).toBeUndefined();
    expect(localStorageContent.token).toBeUndefined();
  });

  test('should NOT expose tokens in response body', async ({ page }) => {
    // Intercept login API request
    let loginResponse = null;

    page.on('response', async (response) => {
      if (response.url().includes('/api/v1/auth/login/')) {
        loginResponse = await response.json().catch(() => null);
      }
    });

    await login(page);

    // Wait a bit for response to be captured
    await page.waitForTimeout(1000);

    // Verify response body does NOT contain tokens
    if (loginResponse) {
      expect(loginResponse.access).toBeUndefined();
      expect(loginResponse.refresh).toBeUndefined();
      expect(loginResponse.access_token).toBeUndefined();
      expect(loginResponse.refresh_token).toBeUndefined();
    }
  });

  test('should reject invalid credentials', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'networkidle' });
    await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible' });

    // Fill in invalid credentials
    await page.fill('input[name="email"], input[type="email"]', 'invalid@example.com');
    await page.fill('input[name="password"], input[type="password"]', 'wrongpassword');

    // Submit form
    await page.click('button[type="submit"]');

    // Wait for error message
    await page.waitForTimeout(2000);

    // Should still be on login page
    expect(page.url()).toContain('/login');

    // Verify no cookies were set
    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    const refreshToken = cookies.find(c => c.name === 'refresh_token');

    expect(accessToken).toBeFalsy();
    expect(refreshToken).toBeFalsy();
  });

  test('should maintain authentication after page reload', async ({ page }) => {
    await login(page);

    // Reload the page
    await page.reload();

    // Should still be authenticated and on dashboard
    expect(page.url()).toContain('/dashboard');

    // Verify cookies still exist
    const { accessToken, refreshToken } = await verifyJWTCookiesSet(page, expect);
    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();
  });

  test('should work with axios withCredentials', async ({ page }) => {
    await login(page);

    // Make an authenticated API request
    const response = await page.evaluate(async () => {
      const res = await fetch('http://localhost:8000/api/v1/auth/user/', {
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json',
        },
      });

      return {
        status: res.status,
        data: await res.json().catch(() => null),
      };
    });

    // Should get authenticated user data
    expect(response.status).toBe(200);
    expect(response.data).toBeTruthy();
    expect(response.data.user).toBeTruthy();
    expect(response.data.user.email).toBe('test@pythonlearning.studio');
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // This test verifies the frontend handles network errors
    // We can't easily simulate network failures, so we test error handling

    await page.goto('/login', { waitUntil: 'networkidle' });
    await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible' });

    // Fill in credentials but simulate offline mode
    await page.context().setOffline(true);

    await page.fill('input[name="email"], input[type="email"]', 'test@pythonlearning.studio');
    await page.fill('input[name="password"], input[type="password"]', 'testpass123');

    // Try to submit
    await page.click('button[type="submit"]');

    // Wait for error handling
    await page.waitForTimeout(2000);

    // Should still be on login page
    expect(page.url()).toContain('/login');

    // Re-enable network
    await page.context().setOffline(false);
  });
});

test.describe('JWT Cookie Authentication - Cookie Expiration', () => {
  test('should set appropriate cookie expiration times', async ({ page }) => {
    await login(page);

    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    const refreshToken = cookies.find(c => c.name === 'refresh_token');

    // Verify cookies have expiration dates
    expect(accessToken.expires).toBeGreaterThan(0);
    expect(refreshToken.expires).toBeGreaterThan(0);

    // Refresh token should expire later than access token
    expect(refreshToken.expires).toBeGreaterThan(accessToken.expires);

    // Calculate expiration times from now
    const now = Date.now() / 1000; // Convert to seconds
    const accessTokenTTL = accessToken.expires - now;
    const refreshTokenTTL = refreshToken.expires - now;

    // Access token should be valid for approximately 15 minutes (900 seconds)
    // Allow some variance for test execution time
    expect(accessTokenTTL).toBeGreaterThan(840); // At least 14 minutes
    expect(accessTokenTTL).toBeLessThan(960); // At most 16 minutes

    // Refresh token should be valid for approximately 7 days (604800 seconds)
    expect(refreshTokenTTL).toBeGreaterThan(604000); // At least ~7 days
    expect(refreshTokenTTL).toBeLessThan(605600); // At most ~7 days + buffer
  });
});
