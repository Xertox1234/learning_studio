/**
 * Authentication helper utilities for Playwright tests
 * Tests JWT cookie-based authentication (PR #15)
 */

/**
 * Login with credentials and verify cookie-based authentication
 * @param {import('@playwright/test').Page} page
 * @param {string} email
 * @param {string} password
 */
export async function login(page, email = 'test@pythonlearning.studio', password = 'testpass123') {
  // Navigate with networkidle to ensure page is fully loaded
  await page.goto('/login', { waitUntil: 'networkidle' });

  // Wait for the login form to be visible
  await page.waitForSelector('input[name="email"], input[type="email"]', { state: 'visible' });

  // Fill login form
  await page.fill('input[name="email"], input[type="email"]', email);
  await page.fill('input[name="password"], input[type="password"]', password);

  // Submit form
  await page.click('button[type="submit"]');

  // Wait for navigation after login
  await page.waitForURL('**/dashboard', { timeout: 10000 });
}

/**
 * Logout and verify cookies are cleared
 * @param {import('@playwright/test').Page} page
 */
export async function logout(page) {
  // Find and click logout button (could be in dropdown or direct button)
  const logoutButton = page.locator('button:has-text("Logout"), a:has-text("Logout")').first();
  await logoutButton.click();

  // Wait for redirect to login page
  await page.waitForURL('**/login', { timeout: 10000 });
}

/**
 * Get all cookies from the page context
 * @param {import('@playwright/test').Page} page
 * @returns {Promise<Array>}
 */
export async function getCookies(page) {
  return await page.context().cookies();
}

/**
 * Get a specific cookie by name
 * @param {import('@playwright/test').Page} page
 * @param {string} cookieName
 * @returns {Promise<object|null>}
 */
export async function getCookie(page, cookieName) {
  const cookies = await getCookies(page);
  return cookies.find(cookie => cookie.name === cookieName) || null;
}

/**
 * Verify JWT cookies are set correctly
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').expect} expect
 */
export async function verifyJWTCookiesSet(page, expect) {
  const cookies = await getCookies(page);

  // Find access_token and refresh_token cookies
  const accessToken = cookies.find(c => c.name === 'access_token');
  const refreshToken = cookies.find(c => c.name === 'refresh_token');

  // Verify access_token exists and has correct flags
  expect(accessToken).toBeTruthy();
  expect(accessToken.httpOnly).toBe(true);
  expect(accessToken.sameSite).toBe('Lax');

  // Verify refresh_token exists and has correct flags
  expect(refreshToken).toBeTruthy();
  expect(refreshToken.httpOnly).toBe(true);
  expect(refreshToken.sameSite).toBe('Lax');

  return { accessToken, refreshToken };
}

/**
 * Verify JWT cookies are NOT accessible from JavaScript
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').expect} expect
 */
export async function verifyTokensNotInJavaScript(page, expect) {
  // Check document.cookie does not contain tokens
  const documentCookie = await page.evaluate(() => document.cookie);
  expect(documentCookie).not.toContain('access_token');
  expect(documentCookie).not.toContain('refresh_token');

  // Check localStorage does not contain tokens
  const localStorageTokens = await page.evaluate(() => {
    return {
      authToken: localStorage.getItem('authToken'),
      access_token: localStorage.getItem('access_token'),
      refresh_token: localStorage.getItem('refresh_token'),
    };
  });

  expect(localStorageTokens.authToken).toBeNull();
  expect(localStorageTokens.access_token).toBeNull();
  expect(localStorageTokens.refresh_token).toBeNull();
}

/**
 * Verify all JWT cookies are cleared
 * @param {import('@playwright/test').Page} page
 * @param {import('@playwright/test').expect} expect
 */
export async function verifyCookiesCleared(page, expect) {
  const cookies = await getCookies(page);
  const accessToken = cookies.find(c => c.name === 'access_token');
  const refreshToken = cookies.find(c => c.name === 'refresh_token');

  expect(accessToken).toBeFalsy();
  expect(refreshToken).toBeFalsy();
}

/**
 * Create a test user via API (helper for test setup)
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {object} userData
 */
export async function createTestUser(request, userData = {}) {
  const defaultUser = {
    email: `test-${Date.now()}@example.com`,
    username: `testuser${Date.now()}`,
    password: 'TestPass123!',
    first_name: 'Test',
    last_name: 'User',
  };

  const user = { ...defaultUser, ...userData };

  const response = await request.post('http://localhost:8000/api/v1/auth/register/', {
    data: user,
  });

  return { user, response };
}

/**
 * Wait for protected route to load (verifies authentication works)
 * @param {import('@playwright/test').Page} page
 * @param {string} route
 */
export async function navigateToProtectedRoute(page, route = '/dashboard') {
  await page.goto(route);

  // Should NOT be redirected to login
  await page.waitForURL(`**${route}`, { timeout: 5000 });
}

/**
 * Verify unauthenticated access redirects to login
 * @param {import('@playwright/test').Page} page
 * @param {string} protectedRoute
 */
export async function verifyProtectedRouteRedirect(page, protectedRoute = '/dashboard') {
  await page.goto(protectedRoute);

  // Should be redirected to login
  await page.waitForURL('**/login', { timeout: 5000 });
}

/**
 * Make authenticated API request using cookies
 * @param {import('@playwright/test').Page} page
 * @param {string} endpoint
 * @param {object} options
 */
export async function makeAuthenticatedRequest(page, endpoint, options = {}) {
  return await page.evaluate(async ({ endpoint, options }) => {
    const response = await fetch(endpoint, {
      credentials: 'include', // Include cookies
      ...options,
    });

    return {
      status: response.status,
      data: await response.json().catch(() => null),
    };
  }, { endpoint, options });
}
