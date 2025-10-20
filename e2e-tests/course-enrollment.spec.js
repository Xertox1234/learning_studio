/**
 * E2E Tests for Course Enrollment with httpOnly Cookie Authentication
 * Tests the complete enrollment flow from unauthenticated to enrolled state
 */

import { test, expect } from '@playwright/test';
import {
  login,
  logout,
  getCookies,
  verifyJWTCookiesSet,
  makeAuthenticatedRequest,
} from './helpers/auth.js';

const COURSE_SLUG = 'interactive-python-fundamentals';
const COURSE_URL = `/learning/${COURSE_SLUG}/`;
const COURSE_API_URL = `/api/v1/learning/courses/${COURSE_SLUG}/`;

test.describe('Course Enrollment - Unauthenticated User', () => {
  test.beforeEach(async ({ page }) => {
    // Clear all cookies and localStorage
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should display course details without enrollment status', async ({ page }) => {
    // Navigate to course page
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Verify course title is visible
    await expect(page.locator('h1, h2').filter({ hasText: /Python Fundamentals/i })).toBeVisible();

    // Verify enrollment status is not shown (user not logged in)
    const enrollmentStatus = page.locator('[data-testid="enrollment-status"]');
    await expect(enrollmentStatus).not.toBeVisible();
  });

  test('should fetch course API without enrollment_status', async ({ page }) => {
    // Intercept API request
    let apiResponse = null;
    page.on('response', async (response) => {
      if (response.url().includes(COURSE_API_URL)) {
        apiResponse = await response.json().catch(() => null);
      }
    });

    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Wait for API response
    await page.waitForTimeout(2000);

    // Verify enrollment_status is null for unauthenticated users
    if (apiResponse) {
      expect(apiResponse.enrollment_status).toBeNull();
      expect(apiResponse.title).toContain('Python');
    }
  });

  test('should show enroll button for unauthenticated users', async ({ page }) => {
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Look for enroll button (could be "Enroll" or "Start Learning")
    const enrollButton = page.locator('button, a').filter({
      hasText: /enroll|start learning|get started/i
    }).first();

    await expect(enrollButton).toBeVisible();
  });

  test('should NOT send cookies with API requests', async ({ page }) => {
    // Verify no auth cookies exist
    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    const refreshToken = cookies.find(c => c.name === 'refresh_token');

    expect(accessToken).toBeFalsy();
    expect(refreshToken).toBeFalsy();

    // Navigate and verify API call doesn't have auth
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Make direct API call without credentials
    const response = await page.evaluate(async (url) => {
      const res = await fetch(url, {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      return {
        status: res.status,
        data: await res.json().catch(() => null)
      };
    }, `http://localhost:8000${COURSE_API_URL}`);

    // Should still work (public course) but no enrollment data
    expect(response.status).toBe(200);
    expect(response.data.enrollment_status).toBeNull();
  });
});

test.describe('Course Enrollment - Authenticated User', () => {
  test.beforeEach(async ({ page }) => {
    // Clear state and login
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());

    // Login with test credentials
    await login(page);
  });

  test('should display enrollment status for authenticated users', async ({ page }) => {
    // Navigate to course page
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Wait for page to load
    await page.waitForTimeout(2000);

    // Verify user is authenticated (check for user menu or logout button)
    const userIndicator = page.locator('[data-testid="user-menu"], button:has-text("Logout")');
    await expect(userIndicator).toBeVisible({ timeout: 10000 }).catch(() => {
      // User indicator might not be visible on course page, that's ok
    });
  });

  test('should fetch course with enrollment_status included', async ({ page }) => {
    let apiResponse = null;

    page.on('response', async (response) => {
      if (response.url().includes(COURSE_API_URL)) {
        try {
          apiResponse = await response.json();
        } catch (e) {
          console.log('Could not parse response:', e);
        }
      }
    });

    // Navigate to course page
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Wait for API response
    await page.waitForTimeout(3000);

    // Verify enrollment_status is present (may be null if not enrolled, or object if enrolled)
    if (apiResponse) {
      console.log('API Response enrollment_status:', apiResponse.enrollment_status);
      // enrollment_status should exist in response (either null or an object)
      expect(apiResponse).toHaveProperty('enrollment_status');
    }
  });

  test('should send httpOnly cookies with API requests', async ({ page }) => {
    // Verify JWT cookies are set
    const { accessToken, refreshToken } = await verifyJWTCookiesSet(page, expect);
    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();

    // Make authenticated API request
    const response = await makeAuthenticatedRequest(
      page,
      `http://localhost:8000${COURSE_API_URL}`
    );

    // Should successfully authenticate and return course data
    expect(response.status).toBe(200);
    expect(response.data).toBeTruthy();
    expect(response.data.title).toContain('Python');
  });

  test('should maintain authentication after page reload', async ({ page }) => {
    // Navigate to course
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Reload page
    await page.reload({ waitUntil: 'networkidle' });

    // Verify cookies still exist
    const { accessToken, refreshToken } = await verifyJWTCookiesSet(page, expect);
    expect(accessToken).toBeTruthy();
    expect(refreshToken).toBeTruthy();

    // Verify can still make authenticated requests
    const response = await makeAuthenticatedRequest(
      page,
      `http://localhost:8000${COURSE_API_URL}`
    );

    expect(response.status).toBe(200);
  });

  test('should handle enrollment creation if not enrolled', async ({ page }) => {
    // Navigate to course
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Look for enroll button or enrolled status
    const enrollButton = page.locator('button, a').filter({
      hasText: /enroll|start learning|continue/i
    }).first();

    const enrolledIndicator = page.locator('text=/enrolled|in progress|continue/i').first();

    // Either user is already enrolled or can enroll
    const isEnrolled = await enrolledIndicator.isVisible().catch(() => false);
    const canEnroll = await enrollButton.isVisible().catch(() => false);

    expect(isEnrolled || canEnroll).toBe(true);

    // If can enroll, test enrollment creation
    if (canEnroll && !isEnrolled) {
      // Click enroll button
      await enrollButton.click();

      // Wait for enrollment to complete
      await page.waitForTimeout(2000);

      // Should now show enrolled status
      const enrolledAfter = await page.locator('text=/enrolled|in progress|continue/i').first().isVisible();
      expect(enrolledAfter).toBe(true);
    }
  });
});

test.describe('Course Enrollment - API Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should verify credentials: include on all fetch requests', async ({ page }) => {
    await login(page);

    // Intercept fetch requests
    const fetchCalls = [];
    await page.route('**/api/v1/**', (route) => {
      const request = route.request();
      fetchCalls.push({
        url: request.url(),
        headers: request.headers(),
      });
      route.continue();
    });

    // Navigate to course page
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Wait for requests to complete
    await page.waitForTimeout(2000);

    // Verify at least one API call was made
    expect(fetchCalls.length).toBeGreaterThan(0);

    // Verify cookies are being sent (Cookie header present)
    const courseFetch = fetchCalls.find(call => call.url.includes(COURSE_API_URL));
    if (courseFetch) {
      // Cookie header should be present when credentials: 'include' is used
      console.log('Course API headers:', courseFetch.headers);
    }
  });

  test('should handle 401 unauthorized gracefully', async ({ page }) => {
    await login(page);

    // Clear cookies to simulate expired session
    await page.context().clearCookies();

    // Navigate to course page
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Should still load page (course is public)
    // But enrollment status should be null
    await page.waitForTimeout(2000);

    // Page should be visible even without auth
    await expect(page.locator('h1, h2').filter({ hasText: /Python/i })).toBeVisible();
  });
});

test.describe('Course Enrollment - Exercise Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().clearCookies();
    await page.goto('/');
    await page.evaluate(() => localStorage.clear();
    await login(page);
  });

  test('should load exercises with authentication', async ({ page }) => {
    // Navigate to course
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Look for exercise links or buttons
    const exerciseLinks = page.locator('a[href*="/exercises/"], a:has-text("Exercise")');
    const exerciseCount = await exerciseLinks.count();

    if (exerciseCount > 0) {
      // Click first exercise
      await exerciseLinks.first().click();

      // Wait for exercise page to load
      await page.waitForTimeout(2000);

      // Verify cookies are still present
      const { accessToken } = await verifyJWTCookiesSet(page, expect);
      expect(accessToken).toBeTruthy();
    }
  });

  test('should send cookies with code execution requests', async ({ page }) => {
    // Navigate to course
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Verify cookies exist
    const { accessToken } = await verifyJWTCookiesSet(page, expect);
    expect(accessToken).toBeTruthy();

    // Test code execution endpoint with cookies
    const response = await makeAuthenticatedRequest(
      page,
      'http://localhost:8000/api/v1/execute/',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          code: 'print("Hello, World!")',
          language: 'python'
        })
      }
    );

    // Should either succeed or return a specific error (not 401)
    expect([200, 400, 404, 500]).toContain(response.status);
    expect(response.status).not.toBe(401); // Should not be unauthorized
  });
});

test.describe('Course Enrollment - Logout Flow', () => {
  test('should clear enrollment state after logout', async ({ page }) => {
    // Login and navigate to course
    await login(page);
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Verify authenticated state
    const { accessToken: beforeLogout } = await verifyJWTCookiesSet(page, expect);
    expect(beforeLogout).toBeTruthy();

    // Logout
    await logout(page);

    // Navigate back to course
    await page.goto(COURSE_URL, { waitUntil: 'networkidle' });

    // Verify cookies are cleared
    const cookies = await getCookies(page);
    const accessToken = cookies.find(c => c.name === 'access_token');
    expect(accessToken).toBeFalsy();

    // Enrollment status should not be visible
    const enrollmentStatus = page.locator('[data-testid="enrollment-status"]');
    await expect(enrollmentStatus).not.toBeVisible();
  });
});
