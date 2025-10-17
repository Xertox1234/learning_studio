/**
 * E2E Tests for JWT Cookie Authentication - Logout Flow
 * Testing PR #15: Cookie cleanup and localStorage verification
 */

import { test, expect } from '@playwright/test';
import {
  login,
  logout,
  getCookies,
  verifyCookiesCleared,
  verifyTokensNotInJavaScript,
} from './helpers/auth.js';

test.describe('JWT Cookie Authentication - Logout Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Clear all cookies and localStorage before each test
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should successfully logout and clear cookies', async ({ page }) => {
    // Login first
    await login(page);

    // Verify cookies are set
    let cookies = await getCookies(page);
    let accessToken = cookies.find(c => c.name === 'access_token');
    let refreshToken = cookies.find(c => c.name === 'refresh_token');
    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();

    // Logout
    await logout(page);

    // Verify we're on login page
    expect(page.url()).toContain('/login');

    // Verify cookies are cleared
    await verifyCookiesCleared(page, expect);
  });

  test('should clear all authentication cookies on logout', async ({ page }) => {
    await login(page);

    // Logout
    await logout(page);

    // Check all cookies
    const cookies = await getCookies(page);

    // Verify no authentication cookies remain
    const authCookieNames = ['access_token', 'refresh_token', 'access', 'refresh'];
    authCookieNames.forEach(cookieName => {
      const cookie = cookies.find(c => c.name === cookieName);
      expect(cookie).toBeFalsy();
    });
  });

  test('should redirect to login after logout', async ({ page }) => {
    await login(page);

    // Should be on dashboard
    expect(page.url()).toContain('/dashboard');

    // Logout
    await logout(page);

    // Should be redirected to login page
    await page.waitForURL('**/login', { timeout: 5000 });
    expect(page.url()).toContain('/login');
  });

  test('should prevent access to protected routes after logout', async ({ page }) => {
    await login(page);
    await logout(page);

    // Try to access protected route
    await page.goto('/dashboard');

    // Should be redirected to login
    await page.waitForURL('**/login', { timeout: 5000 });
    expect(page.url()).toContain('/login');
  });

  test('should clear localStorage on logout (verify no token remnants)', async ({ page }) => {
    await login(page);
    await logout(page);

    // Verify localStorage is completely clean of tokens
    const localStorageContent = await page.evaluate(() => {
      const items = {};
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        items[key] = localStorage.getItem(key);
      }
      return items;
    });

    // Check for any token-related keys
    const tokenRelatedKeys = Object.keys(localStorageContent).filter(key =>
      key.toLowerCase().includes('token') ||
      key.toLowerCase().includes('auth') ||
      key.toLowerCase().includes('jwt')
    );

    expect(tokenRelatedKeys.length).toBe(0);
  });

  test('should handle logout when already logged out', async ({ page }) => {
    // Navigate to logout endpoint directly without being logged in
    await page.goto('/login');

    // Try to click logout (if visible)
    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');

    if (await logoutButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await logoutButton.click();
    }

    // Should not cause errors and remain on login page
    expect(page.url()).toContain('/login');

    // Verify no cookies exist
    await verifyCookiesCleared(page, expect);
  });

  test('should handle multiple logout attempts gracefully', async ({ page }) => {
    await login(page);

    // Logout once
    await logout(page);

    // Try to logout again (should handle gracefully)
    await page.goto('/');

    const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")');

    if (await logoutButton.isVisible({ timeout: 1000 }).catch(() => false)) {
      await logoutButton.click();
    }

    // Should still be on login or home page
    const url = page.url();
    expect(url.includes('/login') || url === 'http://localhost:3000/').toBe(true);
  });

  test('should logout from one tab and affect other tabs', async ({ browser }) => {
    // Create first page and login
    const page1 = await browser.newPage();
    await page1.goto('/');
    await page1.evaluate(() => localStorage.clear());
    await login(page1);

    // Create second page in same context
    const page2 = await page1.context().newPage();
    await page2.goto('/dashboard');

    // Both pages should be authenticated
    expect(page1.url()).toContain('/dashboard');
    expect(page2.url()).toContain('/dashboard');

    // Logout from first page
    await logout(page1);

    // Try to navigate in second page
    await page2.reload();

    // Second page should also be logged out (cookies cleared)
    await page2.waitForURL('**/login', { timeout: 5000 });
    expect(page2.url()).toContain('/login');

    // Cleanup
    await page1.close();
    await page2.close();
  });
});

test.describe('JWT Cookie Authentication - Session Persistence', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should persist session across browser refresh', async ({ page }) => {
    await login(page);

    // Reload page multiple times
    for (let i = 0; i < 3; i++) {
      await page.reload();
      await page.waitForTimeout(1000);

      // Should still be authenticated
      expect(page.url()).toContain('/dashboard');
    }
  });

  test('should NOT persist session after closing and reopening browser', async ({ browser }) => {
    // Create a new browser context (simulates new browser session)
    const context1 = await browser.newContext();
    const page1 = await context1.newPage();

    await page1.goto('/');
    await page1.evaluate(() => localStorage.clear());
    await login(page1);

    // Verify authenticated
    expect(page1.url()).toContain('/dashboard');

    // Close context (simulates closing browser)
    await context1.close();

    // Create new context (simulates reopening browser)
    const context2 = await browser.newContext();
    const page2 = await context2.newPage();

    await page2.goto('/dashboard');

    // Should NOT be authenticated (cookies don't persist across sessions by default)
    await page2.waitForURL('**/login', { timeout: 5000 });
    expect(page2.url()).toContain('/login');

    await context2.close();
  });

  test('should verify localStorage is never used for authentication', async ({ page }) => {
    // Monitor localStorage throughout the entire flow
    const localStorageChanges = [];

    // Hook into localStorage to track all changes
    await page.addInitScript(() => {
      const originalSetItem = localStorage.setItem;
      const originalRemoveItem = localStorage.removeItem;

      window.__localStorageLog = [];

      localStorage.setItem = function(key, value) {
        window.__localStorageLog.push({ action: 'set', key, value });
        return originalSetItem.apply(this, arguments);
      };

      localStorage.removeItem = function(key) {
        window.__localStorageLog.push({ action: 'remove', key });
        return originalRemoveItem.apply(this, arguments);
      };
    });

    // Perform login flow
    await login(page);

    // Get localStorage log
    const log = await page.evaluate(() => window.__localStorageLog || []);

    // Verify no token-related keys were set in localStorage
    const tokenWrites = log.filter(entry =>
      entry.action === 'set' &&
      (entry.key.toLowerCase().includes('token') ||
       entry.key.toLowerCase().includes('auth') ||
       entry.key.toLowerCase().includes('jwt'))
    );

    expect(tokenWrites.length).toBe(0);
  });
});

test.describe('JWT Cookie Authentication - Security Verification', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should verify tokens are not accessible via JavaScript', async ({ page }) => {
    await login(page);

    // Try various methods to access tokens via JavaScript
    const tokenAccess = await page.evaluate(() => {
      const results = {};

      // Try document.cookie
      results.documentCookie = document.cookie;

      // Try localStorage
      results.localStorage = {
        authToken: localStorage.getItem('authToken'),
        access_token: localStorage.getItem('access_token'),
        refresh_token: localStorage.getItem('refresh_token'),
      };

      // Try sessionStorage
      results.sessionStorage = {
        authToken: sessionStorage.getItem('authToken'),
        access_token: sessionStorage.getItem('access_token'),
        refresh_token: sessionStorage.getItem('refresh_token'),
      };

      return results;
    });

    // Verify tokens are not accessible
    expect(tokenAccess.documentCookie).not.toContain('access_token');
    expect(tokenAccess.documentCookie).not.toContain('refresh_token');

    expect(tokenAccess.localStorage.authToken).toBeNull();
    expect(tokenAccess.localStorage.access_token).toBeNull();
    expect(tokenAccess.localStorage.refresh_token).toBeNull();

    expect(tokenAccess.sessionStorage.authToken).toBeNull();
    expect(tokenAccess.sessionStorage.access_token).toBeNull();
    expect(tokenAccess.sessionStorage.refresh_token).toBeNull();
  });

  test('should verify XSS cannot steal tokens', async ({ page }) => {
    await login(page);

    // Attempt to inject XSS script to steal tokens
    const stolenTokens = await page.evaluate(() => {
      try {
        // Simulate XSS attack trying to steal tokens
        const maliciousScript = `
          window.stolenData = {
            cookies: document.cookie,
            localStorage: JSON.stringify(localStorage),
            sessionStorage: JSON.stringify(sessionStorage),
          };
        `;

        eval(maliciousScript);

        return window.stolenData;
      } catch (e) {
        return { error: e.message };
      }
    });

    // Even if XSS executes, tokens should not be accessible
    if (stolenTokens.cookies) {
      expect(stolenTokens.cookies).not.toContain('access_token');
      expect(stolenTokens.cookies).not.toContain('refresh_token');
    }
  });

  test('should verify cookies have correct path and domain', async ({ page }) => {
    await login(page);

    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    const refreshToken = cookies.find(c => c.name === 'refresh_token');

    // Verify path is set (should be '/' for app-wide cookies)
    expect(accessToken.path).toBe('/');
    expect(refreshToken.path).toBe('/');

    // Verify domain is set correctly (localhost for development)
    expect(accessToken.domain).toContain('localhost');
    expect(refreshToken.domain).toContain('localhost');
  });
});
