---
status: ready
priority: p2
issue_id: "016"
tags: [code-quality, technical-debt, testing]
dependencies: []
source: Code Triage (TODO/FIXME comments)
discovered: 2025-10-19
---

# Fix TODO Placeholder in Mock Exercise Function Name

## Problem Statement

The test exercise interface view uses "TODO" as a placeholder for the `function_name` field in mock exercise data. This creates confusing and unrealistic test data that doesn't properly simulate production behavior.

**Location**: `apps/learning/views.py:298-300`

**Current Code**:
```python
self.function_name = 'TODO'
self.starter_code = 'def TODO(numbers):\n    # Find max number\n    pass'
self.solution_code = 'def TODO(numbers):\n    return max(numbers)'
```

**Impact**:
- Test interface shows `def TODO(numbers):` which is confusing
- Doesn't accurately represent real exercise data structure
- Could mislead developers testing the exercise interface
- Makes it unclear whether "TODO" is intentional or needs fixing
- Poor developer experience when testing/debugging the interface

## Findings

**Discovered by**: Code Triage (TODO/FIXME comment scan)

**Context**:
- This is in a test/demo view (`test_exercise_interface_view`)
- Used to preview the exercise UI without a real exercise
- The exercise is about finding the maximum number in a list
- All other mock data is properly filled in (title, description, etc.)

**Why This Matters**:
1. Test data should be realistic to properly validate UI/UX
2. "TODO" makes it unclear if this is placeholder code that needs work
3. Confuses developers who might try to fix "TODO" thinking it's broken
4. Doesn't help validate function name rendering in the UI

## Proposed Solutions

### Option 1: Use Realistic Function Name (RECOMMENDED)

**Pros**:
- Clear, realistic test data
- Properly represents production use case
- Follows Python naming conventions
- Makes test more valuable for UI validation

**Cons**:
- None

**Effort**: Small (< 5 minutes)
**Risk**: Low (simple text change)

**Implementation**:
```python
self.function_name = 'find_maximum'
self.starter_code = 'def find_maximum(numbers):\n    # Find max number\n    pass'
self.solution_code = 'def find_maximum(numbers):\n    return max(numbers)'
```

Alternative names:
- `get_max` - shorter, still clear
- `max_number` - descriptive
- `find_max` - concise

## Recommended Action

**Use Option 1** with `find_maximum` as the function name. It's descriptive, follows Python conventions, and matches the exercise description ("Find Maximum").

## Technical Details

**Affected Files**:
- `apps/learning/views.py:285-323` (test_exercise_interface_view)
- Specifically lines 298-300

**Related Components**:
- Exercise interface template (uses function_name for display)
- Code editor component (renders starter/solution code)

**Database Changes**: None (mock data only)

**Test Requirements**:
- Manual testing: Visit `/test-exercise-interface/` and verify function name displays correctly
- Visual verification: Code editor should show `def find_maximum(numbers):` instead of `def TODO(numbers):`
- No automated tests needed (this is the test view itself)

## Acceptance Criteria

- [ ] `function_name` changed from "TODO" to a realistic name
- [ ] `starter_code` uses the same function name
- [ ] `solution_code` uses the same function name
- [ ] Manual verification shows improved test interface
- [ ] Function name is consistent across all mock code fields
- [ ] Python naming conventions followed (snake_case)

## Work Log

### 2025-10-19 - Initial Discovery

**By:** Claude Triage System
**Actions:**
- Issue discovered during TODO/FIXME comment scan
- Categorized as P2 (Important) - code quality improvement
- Estimated effort: Small (< 5 minutes)
- Marked as ready to pick up

**Learnings:**
- Test/mock data should be as realistic as possible
- Avoid using "TODO" in code unless it truly marks incomplete work
- Good test data improves developer experience and UI validation

## Notes

- This is a quick win for code quality
- Low risk, high clarity benefit
- Good first issue for someone learning the codebase
- Consider reviewing other mock/test data for similar issues

## References

- **File**: `apps/learning/views.py`
- **Function**: `test_exercise_interface_view` (line 285)
- **Template**: `learning/exercise_interface.html` (uses function_name)
