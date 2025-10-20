---
status: ready
priority: p1
issue_id: "020"
tags: [accessibility, wcag-a, frontend, quick-win]
dependencies: []
---

# Add Skip Navigation Link for Keyboard Users

## Problem Statement

No "skip to main content" link exists, forcing keyboard and screen reader users to tab through 20+ navigation links on every page load. This violates WCAG 2.1 Level A (2.4.1 Bypass Blocks).

**WCAG Criterion**: 2.4.1 Bypass Blocks (Level A)
**Severity**: Critical - WCAG Level A blocker
**Legal Risk**: ADA, Section 508 non-compliance

## Findings

**Discovered during**: Accessibility audit (2025-10-20)

**Affected Components**:
- `frontend/src/components/common/Navbar.jsx`
- `frontend/src/components/common/Layout.jsx`
- All Django templates in `templates/`

**Current Behavior**:
```jsx
// ❌ No skip link - users must tab through entire navbar
<nav className="navbar">
  <div className="nav-links">
    <a href="/courses">Courses</a>
    <a href="/exercises">Exercises</a>
    <a href="/forum">Forum</a>
    {/* 20+ more links */}
  </div>
</nav>
<main>
  {/* Main content here */}
</main>
```

**Impact**:
- **Keyboard users**: Must tab 20+ times to reach main content on every page
- **Screen reader users**: Hear entire navigation menu on every page
- **Time waste**: ~10-15 seconds per page load
- **Legal risk**: WCAG Level A failure blocks accessibility compliance

## Proposed Solutions

### Option 1: React Component with Skip Link (RECOMMENDED)

**Pros**:
- Works across all React SPA pages
- Visually hidden until focused
- Standard accessibility pattern
- Easy to implement

**Cons**: None

**Effort**: 2 hours
**Risk**: Low

**Implementation**:
```jsx
// File: frontend/src/components/common/Layout.jsx
import { useRef } from 'react';

export function Layout({ children }) {
  const mainContentRef = useRef(null);

  return (
    <>
      {/* Skip navigation link */}
      <a
        href="#main-content"
        className="skip-link"
        onClick={(e) => {
          e.preventDefault();
          mainContentRef.current?.focus();
        }}
      >
        Skip to main content
      </a>

      <Navbar />

      <main
        id="main-content"
        ref={mainContentRef}
        tabIndex={-1}
        className="outline-none"
      >
        {children}
      </main>

      <Footer />
    </>
  );
}
```

**CSS**:
```css
/* frontend/src/index.css */
.skip-link {
  position: absolute;
  left: -9999px;
  z-index: 999;
  padding: 1rem 1.5rem;
  background: #000;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  border-radius: 0 0 4px 0;
}

.skip-link:focus {
  left: 0;
  top: 0;
}

/* Ensure no outline on main when focused programmatically */
main:focus {
  outline: none;
}
```

### Option 2: Add to Django Templates (Legacy Support)

For remaining Django templates:
```django
{# templates/base.html #}
<a href="#main-content" class="skip-link">Skip to main content</a>

<nav>...</nav>

<main id="main-content" tabindex="-1">
  {% block content %}{% endblock %}
</main>
```

## Recommended Action

✅ **Option 1** - React component (covers majority of app)
✅ **Option 2** - Django templates (for legacy pages)

## Technical Details

**Affected Files**:
- `frontend/src/components/common/Layout.jsx` (NEW skip link)
- `frontend/src/index.css` (NEW skip link styles)
- `templates/base.html` (if Django templates still used)

**Browser Compatibility**: All modern browsers (IE11+)

## Acceptance Criteria

- [ ] Skip link appears when Tab is pressed on page load
- [ ] Clicking/pressing Enter on skip link moves focus to main content
- [ ] Skip link is visually hidden by default (off-screen)
- [ ] Skip link is visible when focused (keyboard users can see it)
- [ ] Screen readers announce "Skip to main content" link
- [ ] Main content receives focus (programmatic focus)
- [ ] Works on all major pages (home, courses, exercises, forum)
- [ ] Passes automated accessibility tests (axe-core)

## Testing Strategy

```javascript
// Manual keyboard test
// 1. Load any page
// 2. Press Tab once → Skip link should appear at top-left
// 3. Press Enter → Focus moves to main content
// 4. Tab again → Next focusable element after navbar

// Automated test (Playwright)
test('skip navigation link works', async ({ page }) => {
  await page.goto('/');

  // Press Tab to focus skip link
  await page.keyboard.press('Tab');

  const skipLink = page.locator('.skip-link:focus');
  await expect(skipLink).toBeVisible();
  await expect(skipLink).toHaveText('Skip to main content');

  // Press Enter to skip
  await page.keyboard.press('Enter');

  // Main content should be focused
  const mainContent = page.locator('#main-content');
  await expect(mainContent).toBeFocused();

  // Skip link should be hidden again
  const skipLinkHidden = page.locator('.skip-link:not(:focus)');
  await expect(skipLinkHidden).toHaveCSS('left', '-9999px');
});

// Screen reader test
test('skip link announced to screen readers', async ({ page }) => {
  await page.goto('/');

  // Check that skip link has accessible text
  const skipLink = page.locator('.skip-link');
  await expect(skipLink).toHaveAccessibleName('Skip to main content');
});

// Accessibility audit
test('skip link passes axe audit', async ({ page }) => {
  await page.goto('/');

  const results = await page.evaluate(() => {
    return axe.run();
  });

  // Should have no violations related to bypass blocks
  const bypassViolations = results.violations.filter(
    v => v.id === 'bypass'
  );
  expect(bypassViolations).toHaveLength(0);
});
```

## Resources

- WCAG 2.4.1: https://www.w3.org/WAI/WCAG21/Understanding/bypass-blocks
- Skip navigation examples: https://webaim.org/techniques/skipnav/
- WebAIM Skip Nav: https://webaim.org/articles/skipnav/

## Work Log

### 2025-10-20 - Accessibility Audit Discovery
**By:** Claude Code Accessibility Auditor
**Actions:**
- Discovered during WCAG 2.1 Level AA audit
- Identified as Level A blocker (critical)
- Categorized as P1 quick win (2 hours)

**Learnings:**
- One of the most common WCAG failures
- Easy to fix, high impact for keyboard users
- Should be in every web application

## Notes

- This is an **accessibility critical** fix
- **Quick win**: 2 hours, low risk
- Should be completed in Phase 1 (Day 1 afternoon)
- Improves UX for ALL keyboard users, not just screen reader users
- Standard pattern across accessible websites
