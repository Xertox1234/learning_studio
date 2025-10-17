# E2E Testing Guide for PR #15 - JWT Cookie Authentication

This guide provides comprehensive instructions for running Playwright E2E tests to verify the JWT cookie authentication migration (PR #15).

## Overview

PR #15 migrates JWT authentication from localStorage to httpOnly cookies to address **CVE-2024-JWT-003** (XSS-based token theft vulnerability).

### What's Being Tested

1. **Login Flow** - Cookie-based authentication with security flags
2. **Protected Routes** - Access control and authentication persistence
3. **Logout Flow** - Cookie cleanup and session termination
4. **Token Refresh** - Automatic refresh on expiry and token rotation
5. **Security Verification** - XSS protection and localStorage cleanup

## Prerequisites

### 1. Install Playwright Browsers

```bash
npx playwright install
```

This downloads Chromium, Firefox, and WebKit browsers for testing.

### 2. Environment Setup

Ensure you have a test user in your database:

```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py createsuperuser
```

**Test Credentials:**
- Email: `test@pythonlearning.studio`
- Password: `testpass123`

Alternatively, the tests can create users dynamically using the registration API.

### 3. Start Development Servers

The Playwright configuration will automatically start both servers, but you can also start them manually:

**Terminal 1 - Django Backend:**
```bash
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver
```

**Terminal 2 - React Frontend:**
```bash
cd frontend && npm run dev
```

Wait for both servers to be ready before running tests.

## Running Tests

### Quick Start - Run All Tests

```bash
# Run all E2E tests (headless mode)
npm run test:e2e

# Or use npx directly
npx playwright test
```

### Test Modes

#### 1. UI Mode (Recommended for Development)

```bash
npm run test:e2e:ui
```

**Features:**
- Interactive test runner
- Watch mode - tests rerun on file changes
- Time travel debugging
- Visual test explorer
- Live test execution view

#### 2. Headed Mode (See Browser)

```bash
npm run test:e2e:headed
```

Shows browser window during test execution. Useful for debugging visual issues.

#### 3. Debug Mode

```bash
npm run test:e2e:debug
```

**Features:**
- Step through tests line by line
- Pause on failures
- Inspect page state
- Use Playwright Inspector

#### 4. Specific Browser

```bash
# Test on specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit

# Test on mobile
npx playwright test --project="Mobile Chrome"
npx playwright test --project="Mobile Safari"
```

### Running Specific Test Files

```bash
# Login tests only
npx playwright test e2e-tests/auth-login.spec.js

# Protected routes tests only
npx playwright test e2e-tests/auth-protected-routes.spec.js

# Logout tests only
npx playwright test e2e-tests/auth-logout.spec.js

# Token refresh tests only
npx playwright test e2e-tests/auth-token-refresh.spec.js
```

### Running Specific Tests

```bash
# Run tests matching a pattern
npx playwright test -g "should successfully login"

# Run tests in a specific describe block
npx playwright test -g "Login Flow"

# Run a single test
npx playwright test -g "should set httpOnly cookies on successful login"
```

### Test Filtering

```bash
# Run only tests marked as .only
npx playwright test --grep-invert "@skip"

# Skip specific tests
npx playwright test --grep-invert "network errors"
```

## Test Reports

### View HTML Report

After running tests:

```bash
npm run test:e2e:report

# Or
npx playwright show-report
```

The HTML report includes:
- Test results with pass/fail status
- Screenshots on failure
- Videos of failed tests
- Traces for debugging
- Execution timeline

### Report Location

Reports are saved to `playwright-report/index.html`

### Trace Viewer

Open traces for failed tests:

```bash
npx playwright show-trace test-results/.../trace.zip
```

Traces include:
- DOM snapshots at each step
- Network activity
- Console logs
- Screenshots
- Action log

## Test Coverage

### Authentication Flow Tests (auth-login.spec.js)

- ✅ Successful login with valid credentials
- ✅ httpOnly cookies set on login
- ✅ Cookie security flags (httpOnly, SameSite, Secure)
- ✅ Tokens NOT exposed in JavaScript
- ✅ Tokens NOT stored in localStorage
- ✅ Tokens NOT in response body
- ✅ Invalid credentials rejected
- ✅ Authentication persists after reload
- ✅ Axios withCredentials works
- ✅ Network error handling
- ✅ Cookie expiration times

**Expected Results:**
- All cookies have `httpOnly: true`
- `document.cookie` does NOT show tokens
- `localStorage` does NOT contain tokens
- Access token expires in ~5 minutes
- Refresh token expires in ~24 hours

### Protected Routes Tests (auth-protected-routes.spec.js)

- ✅ Access to protected routes when authenticated
- ✅ Redirect to login when unauthenticated
- ✅ Authentication persists across navigation
- ✅ Authentication persists after page refresh
- ✅ Deep links handled correctly
- ✅ Original URL remembered after login
- ✅ API requests include cookies
- ✅ CSRF token automatically included
- ✅ Browser back/forward buttons work
- ✅ Multiple tabs share authentication

**Expected Results:**
- Protected routes accessible when logged in
- Redirects to `/login` when not authenticated
- Cookies maintained across navigation
- CSRF tokens sent with mutations

### Logout Tests (auth-logout.spec.js)

- ✅ Successful logout clears cookies
- ✅ All auth cookies removed
- ✅ Redirect to login after logout
- ✅ Protected routes blocked after logout
- ✅ localStorage cleaned on logout
- ✅ Handle logout when already logged out
- ✅ Multiple logout attempts graceful
- ✅ Logout affects all tabs
- ✅ Session persists across refresh
- ✅ Session NOT persisted across browser restart
- ✅ localStorage never used for auth
- ✅ Tokens not accessible via JavaScript
- ✅ XSS cannot steal tokens
- ✅ Cookies have correct path and domain

**Expected Results:**
- All authentication cookies deleted
- Cannot access protected routes
- Redirected to login page
- No token data in localStorage or sessionStorage
- XSS scripts cannot access tokens

### Token Refresh Tests (auth-token-refresh.spec.js)

- ✅ Automatic refresh on 401 response
- ✅ Authentication maintained after access token expires
- ✅ Refresh token used to get new access token
- ✅ Refresh token expiration handled gracefully
- ✅ Refresh token rotated on use
- ✅ Refresh requests include cookies
- ✅ Concurrent requests during refresh
- ✅ Old tokens invalidated after refresh
- ✅ Old refresh token rejected after rotation
- ✅ Network errors during refresh handled
- ✅ Malformed refresh response handled

**Expected Results:**
- New access token obtained automatically
- Refresh token rotates on use
- Old tokens blacklisted
- Graceful degradation on errors

## Debugging Failed Tests

### 1. Check Screenshot

Failed tests automatically capture screenshots:

```bash
open test-results/[test-name]/test-failed-1.png
```

### 2. Watch Video

Failed tests record video:

```bash
open test-results/[test-name]/video.webm
```

### 3. Open Trace

Most detailed debugging information:

```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

### 4. Run in Debug Mode

```bash
npx playwright test --debug -g "failing test name"
```

### 5. Add Debugging Code

```javascript
// Pause test execution
await page.pause();

// Take screenshot manually
await page.screenshot({ path: 'debug.png' });

// Print page content
console.log(await page.content());

// Print console logs
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

## Common Issues

### 1. Servers Not Running

**Error:** `Error: connect ECONNREFUSED ::1:8000`

**Solution:**
```bash
# Start Django server
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver

# Start React server
cd frontend && npm run dev
```

### 2. Test User Not Found

**Error:** Login fails with 401

**Solution:**
```bash
# Create test user
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py createsuperuser

# Email: test@pythonlearning.studio
# Password: testpass123
```

### 3. Port Already in Use

**Error:** `Error: Port 3000 is already in use`

**Solution:**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### 4. Cookies Not Being Set

**Issue:** Tests fail because cookies aren't set

**Debug Steps:**
1. Check Django backend logs for errors
2. Verify CORS settings in `settings/base.py`
3. Ensure `CSRF_TRUSTED_ORIGINS` includes frontend URL
4. Check browser console in headed mode

### 5. CSRF Token Issues

**Issue:** POST requests fail with CSRF errors

**Debug:**
```javascript
// Add to test
const cookies = await page.context().cookies();
console.log('Cookies:', cookies);

const csrfToken = await page.evaluate(() => {
  return document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
});
console.log('CSRF Token:', csrfToken);
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          npm install
          cd frontend && npm install

      - name: Install Playwright Browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Best Practices

### 1. Isolate Tests

Each test should be independent:
- Clear cookies before each test
- Clear localStorage before each test
- Don't rely on test execution order

### 2. Use Descriptive Test Names

```javascript
// Good
test('should set httpOnly cookies on successful login', ...)

// Bad
test('login test', ...)
```

### 3. Wait for Elements Properly

```javascript
// Good - wait for specific condition
await page.waitForURL('**/dashboard', { timeout: 5000 });

// Bad - arbitrary timeout
await page.waitForTimeout(5000);
```

### 4. Use Page Object Pattern

For complex pages, create page objects:

```javascript
// pages/LoginPage.js
export class LoginPage {
  constructor(page) {
    this.page = page;
  }

  async login(email, password) {
    await this.page.fill('input[name="email"]', email);
    await this.page.fill('input[name="password"]', password);
    await this.page.click('button[type="submit"]');
  }
}
```

## Code Generation

Generate test code by recording browser interactions:

```bash
npm run test:e2e:codegen
```

This opens a browser where you can:
1. Interact with your app
2. Playwright records your actions
3. Copy generated test code

## Additional Resources

- [Playwright Documentation](https://playwright.dev)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging Playwright Tests](https://playwright.dev/docs/debug)
- [PR #15 - JWT Cookie Migration](https://github.com/Xertox1234/learning_studio/pull/15)
- [CVE-2024-JWT-003 Details](./COMPREHENSIVE_SECURITY_AUDIT_2025.md)

## Manual Testing Checklist

For manual verification beyond automated tests:

### Backend Testing

- [ ] Login with valid credentials → cookies set
- [ ] Login with invalid credentials → 401 error
- [ ] Access protected endpoint → authenticated
- [ ] Token refresh → new access token in cookie
- [ ] Logout → cookies deleted
- [ ] After logout → authentication fails

### Frontend Testing

- [ ] Login → redirected to dashboard
- [ ] Page refresh → still authenticated
- [ ] Protected routes → accessible when logged in
- [ ] Protected routes → redirected when logged out
- [ ] Token expiry → automatic refresh
- [ ] Logout → redirected to login page
- [ ] Check browser DevTools → cookies have httpOnly flag
- [ ] Check browser console → `document.cookie` does NOT show tokens

### Browser Compatibility

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari
- [ ] Mobile browsers (iOS Safari, Chrome Mobile)

## Support

If you encounter issues:

1. Check test output and screenshots
2. Run tests in debug mode
3. Review Django server logs
4. Check browser console (headed mode)
5. Verify environment configuration
6. Review PR #15 implementation details

---

**Note:** These tests are specifically designed to verify PR #15 (JWT cookie migration). They ensure that:
- Tokens are stored in httpOnly cookies (not localStorage)
- Cookies have proper security flags
- XSS attacks cannot steal tokens
- Token refresh works correctly
- Logout properly cleans up session data
