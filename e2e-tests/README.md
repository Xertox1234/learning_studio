# E2E Tests - JWT Cookie Authentication (PR #15)

Comprehensive Playwright E2E tests for JWT cookie-based authentication migration.

## Quick Start

```bash
# Install browsers (first time only)
npx playwright install

# Run all tests
npm run test:e2e

# Run with UI (recommended)
npm run test:e2e:ui

# View report
npm run test:e2e:report
```

## Test Files

### 1. `auth-login.spec.js`
Tests login flow and cookie security:
- Login with valid/invalid credentials
- httpOnly cookie flags verification
- Token security (not accessible from JS)
- localStorage verification
- Cookie expiration times

### 2. `auth-protected-routes.spec.js`
Tests protected route access:
- Authenticated route access
- Unauthenticated redirects
- Navigation persistence
- API request authentication
- CSRF token handling
- Multi-tab authentication

### 3. `auth-logout.spec.js`
Tests logout flow and cleanup:
- Cookie deletion on logout
- Redirect to login
- localStorage cleanup
- Session persistence verification
- XSS protection verification
- Multi-tab logout

### 4. `auth-token-refresh.spec.js`
Tests automatic token refresh:
- Refresh on 401 response
- Token rotation
- Refresh token usage
- Token blacklisting
- Error handling
- Concurrent requests

## Helper Utilities

### `helpers/auth.js`

Common authentication utilities:

```javascript
import { login, logout, verifyJWTCookiesSet } from './helpers/auth.js';

// Login with default test user
await login(page);

// Login with custom credentials
await login(page, 'custom@email.com', 'password');

// Logout
await logout(page);

// Verify cookies are set correctly
await verifyJWTCookiesSet(page, expect);

// Get all cookies
const cookies = await getCookies(page);

// Verify tokens not in JavaScript
await verifyTokensNotInJavaScript(page, expect);
```

## Running Tests

### All Tests
```bash
npm run test:e2e
```

### Specific File
```bash
npx playwright test e2e-tests/auth-login.spec.js
```

### Specific Test
```bash
npx playwright test -g "should set httpOnly cookies"
```

### Debug Mode
```bash
npm run test:e2e:debug
```

### Headed Mode (See Browser)
```bash
npm run test:e2e:headed
```

## Test Coverage

**Total Tests:** 50+ comprehensive tests

**Categories:**
- Login Flow: 12 tests
- Protected Routes: 15 tests
- Logout Flow: 18 tests
- Token Refresh: 12 tests

**Security Verifications:**
- ✅ httpOnly cookies
- ✅ SameSite protection
- ✅ No localStorage tokens
- ✅ XSS protection
- ✅ CSRF tokens
- ✅ Token rotation
- ✅ Token blacklisting

## Test Structure

```
e2e-tests/
├── auth-login.spec.js           # Login and cookie setup
├── auth-protected-routes.spec.js # Route protection
├── auth-logout.spec.js          # Logout and cleanup
├── auth-token-refresh.spec.js   # Token refresh logic
├── helpers/
│   └── auth.js                  # Shared utilities
└── README.md                    # This file
```

## Prerequisites

1. **Test User Required:**
   ```bash
   DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py createsuperuser
   ```
   - Email: `test@pythonlearning.studio`
   - Password: `testpass123`

2. **Servers Running:**
   - Django: http://localhost:8000
   - React: http://localhost:3000

3. **Playwright Browsers:**
   ```bash
   npx playwright install
   ```

## Configuration

See `playwright.config.js` in project root for:
- Browser configurations
- Test timeouts
- Reporter settings
- Server startup

## Debugging

### View Screenshots
Failed tests save screenshots to `test-results/`

### View Videos
```bash
open test-results/[test-name]/video.webm
```

### View Traces
```bash
npx playwright show-trace test-results/[test-name]/trace.zip
```

### Add Debug Points
```javascript
await page.pause(); // Pause test
await page.screenshot({ path: 'debug.png' }); // Screenshot
console.log(await page.content()); // Page HTML
```

## Common Issues

### Servers Not Running
Start both Django and React servers before testing.

### Test User Not Found
Create test user with email `test@pythonlearning.studio`.

### Port Conflicts
Kill processes on ports 3000 and 8000.

### Cookies Not Set
Check Django CORS and CSRF settings.

## Best Practices

1. **Isolation:** Each test clears cookies and localStorage
2. **Waiting:** Use `waitForURL` instead of `waitForTimeout`
3. **Assertions:** Verify both success and security properties
4. **Errors:** Test both happy path and error cases

## Documentation

For detailed information, see:
- [E2E Test Guide](../E2E_TEST_GUIDE.md) - Complete testing guide
- [Playwright Config](../playwright.config.js) - Test configuration
- [PR #15](https://github.com/Xertox1234/learning_studio/pull/15) - Implementation details

## What's Being Tested

This test suite verifies **CVE-2024-JWT-003** fix:

**Before (Vulnerable):**
- Tokens stored in localStorage
- Accessible to JavaScript
- Vulnerable to XSS attacks

**After (Secure):**
- Tokens in httpOnly cookies
- NOT accessible to JavaScript
- Protected from XSS
- SameSite CSRF protection
- Automatic token rotation
- Token blacklisting

## Test Data

### Default Test User
- Email: `test@pythonlearning.studio`
- Password: `testpass123`

### Protected Routes Tested
- `/dashboard`
- `/courses`
- `/exercises`
- `/profile`

### API Endpoints Tested
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/user/`

## Expected Cookie Properties

```javascript
{
  name: 'access_token',
  httpOnly: true,        // NOT accessible to JavaScript
  sameSite: 'Lax',      // CSRF protection
  secure: true,         // HTTPS only (production)
  expires: ~5 minutes
}

{
  name: 'refresh_token',
  httpOnly: true,
  sameSite: 'Lax',
  secure: true,
  expires: ~24 hours
}
```

## Continuous Integration

Tests can run in CI/CD:

```yaml
- name: Run E2E Tests
  run: npm run test:e2e

- name: Upload Report
  uses: actions/upload-artifact@v3
  with:
    name: playwright-report
    path: playwright-report/
```

## Contributing

When adding new tests:

1. Follow existing naming conventions
2. Use helper utilities from `helpers/auth.js`
3. Clear state in `beforeEach`
4. Add descriptive test names
5. Test both success and failure cases
6. Update this README with new tests

## Support

For issues or questions:
1. Check test output and screenshots
2. Run in debug mode: `npm run test:e2e:debug`
3. Review [E2E Test Guide](../E2E_TEST_GUIDE.md)
4. Check Django server logs
5. Verify environment configuration
