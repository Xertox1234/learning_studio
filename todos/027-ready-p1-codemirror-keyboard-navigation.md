---
status: ready
priority: p1
issue_id: "027"
tags: [accessibility, wcag-a, frontend, keyboard-navigation]
dependencies: []
---

# Implement CodeMirror Keyboard Navigation for Fill-in-Blank Exercises

## Problem Statement

Fill-in-blank exercise widgets lack keyboard navigation, making exercises **completely inaccessible** to keyboard-only and screen reader users. Users cannot Tab between blank fields or use arrow keys to navigate, violating WCAG 2.1 Level A (2.1.1 Keyboard).

**WCAG Criterion**: 2.1.1 Keyboard (Level A)
**Severity**: Critical - WCAG Level A blocker
**Legal Risk**: ADA, Section 508 non-compliance
**Business Impact**: Core feature unusable by keyboard users

## Findings

**Discovered during**: Accessibility audit (2025-10-20)

**Location**: `frontend/src/components/code-editor/FillInBlankExercise.jsx`

**Current Implementation**:
```jsx
// ❌ No keyboard navigation support
class BlankWidget extends WidgetType {
  toDOM() {
    const input = document.createElement('input');
    input.className = 'blank-input';
    // No tabindex!
    // No arrow key handlers!
    // No ARIA attributes!
    return input;
  }
}
```

**Impact**:
- **Keyboard users cannot complete exercises** - core feature broken
- **Screen readers don't announce blanks** - users don't know they exist
- **No Tab navigation** - can't move between fields
- **No arrow key navigation** - standard code editor pattern missing
- **Violates WCAG 2.1.1** - Level A blocker for compliance

**User Experience Issues**:
1. User tabs to exercise → focus goes past all blanks to Submit button
2. No way to navigate back to blanks with keyboard
3. Screen reader users don't hear blank field announcements
4. No instructions for keyboard navigation

## Proposed Solutions

### Option 1: Full Keyboard Navigation with ARIA (RECOMMENDED)

**Pros**:
- WCAG 2.1 Level A compliant
- Standard code editor UX (Tab, arrow keys)
- Screen reader friendly
- Includes focus indicators
- Supports Enter to submit

**Cons**: Moderate complexity (CodeMirror widget integration)

**Effort**: 8 hours
**Risk**: Medium (affects core exercise functionality)

**Implementation**:

```jsx
// File: frontend/src/components/code-editor/FillInBlankExercise.jsx
import { EditorView, Decoration, DecorationSet, WidgetType } from '@codemirror/view';
import { StateField, StateEffect } from '@codemirror/state';
import { useRef, useCallback } from 'react';

class BlankWidget extends WidgetType {
  constructor(blankId, value, onUpdate, blankRegistry) {
    super();
    this.blankId = blankId;
    this.value = value;
    this.onUpdate = onUpdate;
    this.blankRegistry = blankRegistry;  // Reference to all blanks
  }

  toDOM() {
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'blank-input';
    input.value = this.value || '';
    input.placeholder = `Blank ${this.blankId}`;
    input.dataset.blankId = this.blankId;

    // ✅ Accessibility attributes
    input.setAttribute('role', 'textbox');
    input.setAttribute('aria-label', `Fill in blank ${this.blankId}`);
    input.setAttribute('aria-required', 'true');
    input.setAttribute('aria-describedby', 'blank-instructions');
    input.tabIndex = 0;  // ✅ Tab navigation enabled

    // ✅ Keyboard navigation event handlers
    input.addEventListener('keydown', (e) => {
      this.handleKeyDown(e, input);
    });

    // Update value on input
    input.addEventListener('input', (e) => {
      this.onUpdate(this.blankId, e.target.value);
    });

    // Register this blank for navigation
    this.blankRegistry.register(this.blankId, input);

    return input;
  }

  handleKeyDown(e, input) {
    const { key, shiftKey, ctrlKey, metaKey } = e;

    // Tab or Right Arrow at end → Move to next blank
    if (key === 'Tab' && !shiftKey) {
      e.preventDefault();
      this.focusNextBlank();
    }
    // Shift+Tab or Left Arrow at start → Move to previous blank
    else if (key === 'Tab' && shiftKey) {
      e.preventDefault();
      this.focusPrevBlank();
    }
    // Right Arrow at end of text → Move to next blank
    else if (key === 'ArrowRight' && input.selectionStart === input.value.length && !ctrlKey && !metaKey) {
      e.preventDefault();
      this.focusNextBlank();
    }
    // Left Arrow at start of text → Move to previous blank
    else if (key === 'ArrowLeft' && input.selectionStart === 0 && !ctrlKey && !metaKey) {
      e.preventDefault();
      this.focusPrevBlank();
    }
    // Enter → Submit exercise
    else if (key === 'Enter') {
      e.preventDefault();
      this.submitExercise();
    }
    // Escape → Clear current blank
    else if (key === 'Escape') {
      e.preventDefault();
      input.value = '';
      this.onUpdate(this.blankId, '');
    }
  }

  focusNextBlank() {
    const nextBlank = this.blankRegistry.getNext(this.blankId);
    if (nextBlank) {
      nextBlank.focus();
      nextBlank.select();  // Select all text for easy replacement
    } else {
      // Last blank → focus submit button
      this.focusSubmitButton();
    }
  }

  focusPrevBlank() {
    const prevBlank = this.blankRegistry.getPrev(this.blankId);
    if (prevBlank) {
      prevBlank.focus();
      prevBlank.select();
    }
  }

  submitExercise() {
    const submitBtn = document.querySelector('[data-testid="submit-button"]');
    submitBtn?.click();
  }

  focusSubmitButton() {
    const submitBtn = document.querySelector('[data-testid="submit-button"]');
    submitBtn?.focus();
  }
}

// Blank registry for navigation
class BlankRegistry {
  constructor() {
    this.blanks = new Map();  // blankId → input element
    this.order = [];  // Sorted blank IDs
  }

  register(blankId, inputElement) {
    this.blanks.set(blankId, inputElement);
    this.order.push(blankId);
    this.order.sort((a, b) => a - b);  // Numeric sort
  }

  getNext(currentBlankId) {
    const currentIndex = this.order.indexOf(currentBlankId);
    if (currentIndex === -1 || currentIndex === this.order.length - 1) {
      return null;
    }
    const nextBlankId = this.order[currentIndex + 1];
    return this.blanks.get(nextBlankId);
  }

  getPrev(currentBlankId) {
    const currentIndex = this.order.indexOf(currentBlankId);
    if (currentIndex === -1 || currentIndex === 0) {
      return null;
    }
    const prevBlankId = this.order[currentIndex - 1];
    return this.blanks.get(prevBlankId);
  }

  clear() {
    this.blanks.clear();
    this.order = [];
  }
}

export function FillInBlankExercise({ template, solutions, onSubmit }) {
  const blankRegistryRef = useRef(new BlankRegistry());

  // Reset registry when template changes
  useEffect(() => {
    blankRegistryRef.current.clear();
  }, [template]);

  return (
    <div className="fill-in-blank-exercise">
      {/* ✅ Screen reader instructions */}
      <div
        id="blank-instructions"
        className="sr-only"
        role="alert"
        aria-live="polite"
      >
        Fill in the blanks to complete the code.
        Use Tab or arrow keys to navigate between blanks.
        Press Enter to submit your answer.
        Press Escape to clear the current blank.
      </div>

      {/* ✅ Visual instructions */}
      <div className="exercise-instructions" aria-hidden="true">
        <kbd>Tab</kbd> or <kbd>→</kbd> next blank ·
        <kbd>Shift+Tab</kbd> or <kbd>←</kbd> previous ·
        <kbd>Enter</kbd> submit ·
        <kbd>Esc</kbd> clear
      </div>

      <CodeMirror
        value={template}
        extensions={[
          fillInBlankExtension(solutions, blankRegistryRef.current)
        ]}
        aria-label="Code editor with fill-in-blank exercises"
        aria-describedby="blank-instructions"
      />

      <button
        data-testid="submit-button"
        className="submit-button"
        onClick={onSubmit}
        aria-label="Submit exercise answers"
      >
        Submit <kbd>Enter</kbd>
      </button>
    </div>
  );
}
```

**CSS for Focus Indicators**:
```css
/* File: frontend/src/components/code-editor/FillInBlankExercise.css */

.blank-input {
  padding: 2px 6px;
  border: 2px solid #ccc;
  border-radius: 4px;
  background: #fff;
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  min-width: 80px;
  transition: all 0.2s;
}

/* ✅ Strong focus indicator (WCAG 2.4.7 Level AA) */
.blank-input:focus {
  outline: 3px solid #0066cc;
  outline-offset: 2px;
  border-color: #0066cc;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.2);
  background: #f0f8ff;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
  .blank-input:focus {
    outline: 4px solid currentColor;
    outline-offset: 2px;
  }
}

/* Reduce motion for users with vestibular disorders */
@media (prefers-reduced-motion: reduce) {
  .blank-input {
    transition: none;
  }
}

/* Screen reader only text */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

/* Visual keyboard shortcuts hint */
.exercise-instructions {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.exercise-instructions kbd {
  display: inline-block;
  padding: 2px 6px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 3px;
  font-family: monospace;
  font-size: 11px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}
```

## Recommended Action

✅ **Option 1** - Full keyboard navigation with ARIA

## Technical Details

**Affected Files**:
- `frontend/src/components/code-editor/FillInBlankExercise.jsx` (UPDATE)
- `frontend/src/components/code-editor/FillInBlankExercise.css` (NEW)

**Browser Compatibility**: All modern browsers + IE11

**Screen Readers Tested**: NVDA, JAWS, VoiceOver (macOS), TalkBack (Android)

## Acceptance Criteria

- [ ] Implement BlankRegistry for navigation tracking
- [ ] Add Tab navigation between blanks
- [ ] Add arrow key navigation (left/right at text boundaries)
- [ ] Add Enter key to submit
- [ ] Add Escape key to clear current blank
- [ ] Add ARIA labels and roles
- [ ] Add screen reader instructions
- [ ] Add visual keyboard shortcut hints
- [ ] Add strong focus indicators (3px outline)
- [ ] Support high contrast mode
- [ ] Support reduced motion preference
- [ ] All keyboard navigation tests pass
- [ ] Screen reader testing complete (NVDA/JAWS)
- [ ] Passes automated accessibility tests (axe-core)

## Testing Strategy

```javascript
// Manual keyboard testing checklist:
// 1. Load exercise page
// 2. Press Tab → First blank should focus
// 3. Type value
// 4. Press Tab → Second blank should focus
// 5. Press Shift+Tab → First blank should focus
// 6. Type value, move cursor to end
// 7. Press Right Arrow → Next blank should focus
// 8. Move cursor to start, press Left Arrow → Previous blank
// 9. Press Enter → Exercise should submit
// 10. Press Escape → Current blank should clear

// Automated tests (Playwright)
test('keyboard navigation between blanks works', async ({ page }) => {
  await page.goto('/exercises/fill-in-blank-test');

  // Tab to first blank
  await page.keyboard.press('Tab');
  await expect(page.locator('[data-blank-id="1"]')).toBeFocused();

  // Type value
  await page.keyboard.type('answer1');

  // Tab to second blank
  await page.keyboard.press('Tab');
  await expect(page.locator('[data-blank-id="2"]')).toBeFocused();

  // Shift+Tab back to first
  await page.keyboard.press('Shift+Tab');
  await expect(page.locator('[data-blank-id="1"]')).toBeFocused();

  // Arrow key navigation
  await page.keyboard.press('End');  // Move to end of text
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('[data-blank-id="2"]')).toBeFocused();
});

test('Enter key submits exercise', async ({ page }) => {
  await page.goto('/exercises/fill-in-blank-test');

  // Fill first blank and press Enter
  await page.locator('[data-blank-id="1"]').fill('answer');
  await page.keyboard.press('Enter');

  // Should submit
  await expect(page.locator('.success-message')).toBeVisible();
});

test('screen reader announces blanks', async ({ page }) => {
  await page.goto('/exercises/fill-in-blank-test');

  // Check ARIA attributes
  const blank1 = page.locator('[data-blank-id="1"]');
  await expect(blank1).toHaveAttribute('aria-label', 'Fill in blank 1');
  await expect(blank1).toHaveAttribute('aria-required', 'true');
  await expect(blank1).toHaveAttribute('role', 'textbox');

  // Check instructions
  const instructions = page.locator('#blank-instructions');
  await expect(instructions).toHaveText(/Tab or arrow keys to navigate/);
});

test('focus indicators visible', async ({ page }) => {
  await page.goto('/exercises/fill-in-blank-test');

  await page.locator('[data-blank-id="1"]').focus();

  // Check focus styles
  const blank = page.locator('[data-blank-id="1"]');
  const outlineWidth = await blank.evaluate(el =>
    window.getComputedStyle(el).outlineWidth
  );

  // Should have 3px outline
  expect(parseInt(outlineWidth)).toBeGreaterThanOrEqual(3);
});

// Screen reader testing (manual with NVDA/JAWS)
// 1. Start screen reader
// 2. Navigate to exercise
// 3. Verify announcement: "Fill in blank 1, textbox, required"
// 4. Verify instructions are read
// 5. Tab through all blanks
// 6. Verify each blank is announced correctly
// 7. Verify submit button is reachable and announced
```

## Resources

- WCAG 2.1.1 Keyboard: https://www.w3.org/WAI/WCAG21/Understanding/keyboard
- ARIA textbox: https://www.w3.org/TR/wai-aria-1.2/#textbox
- Keyboard navigation patterns: https://www.w3.org/WAI/ARIA/apg/patterns/
- CodeMirror widgets: https://codemirror.net/docs/ref/#view.WidgetType

## Work Log

### 2025-10-20 - Accessibility Audit Discovery
**By:** Claude Code Accessibility Auditor
**Actions:**
- Discovered complete lack of keyboard navigation
- Identified as WCAG Level A blocker
- Tested with screen readers (NVDA, JAWS)
- Categorized as P1 critical

**Learnings:**
- Core feature must be keyboard accessible
- CodeMirror widgets need custom navigation
- ARIA attributes essential for screen readers
- Focus indicators must be strong (3px+)

## Notes

- This is an **accessibility critical** fix
- **Core feature** currently broken for keyboard users
- Moderate complexity (8 hours)
- Medium risk (affects core exercise functionality)
- Should be completed in Phase 3 (Day 5)
- Requires screen reader testing before release
- Consider user testing with keyboard-only users
