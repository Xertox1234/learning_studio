---
status: ready
priority: p1
issue_id: "019"
tags: [code-review, data-integrity, bug, django]
dependencies: []
---

# Fix Mutable Default in JSONField Migration

## Problem Statement

JSONField uses mutable default (`default=list`) which causes data corruption. All model instances share the SAME list object in memory, leading to cross-contamination of data.

**Category**: Data Integrity / Data Corruption
**Severity**: Critical (P1)

## Findings

**Discovered during**: Data integrity review (2025-10-20)

**Vulnerable Code Pattern**:
```python
# ❌ DANGEROUS: Mutable default shared across instances
structured_content = models.JSONField(default=list)
# All instances share the SAME list object in memory!
```

**Impact**:
- **Data corruption**: Changes to one object affect all objects
- **Hard-to-debug issues**: Intermittent, state-dependent bugs
- **Database integrity compromised**: Unpredictable data behavior

**Example of Problem**:
```python
lesson1 = Lesson.objects.create(title="Lesson 1")
lesson2 = Lesson.objects.create(title="Lesson 2")

lesson1.structured_content.append({"type": "text"})
lesson1.save()

lesson2.refresh_from_db()
# 🚨 BUG: lesson2.structured_content now contains lesson1's data!
```

## Proposed Solutions

### Option 1: Use Callable Default (RECOMMENDED)

**Pros**:
- Standard Django pattern
- No custom code needed
- Each instance gets new list
- Simple migration

**Cons**: None

**Effort**: 2 hours
**Risk**: Low

**Implementation**:
```python
# Step 1: Update model definition
# apps/learning/models.py
class Lesson(models.Model):
    structured_content = models.JSONField(default=list, blank=True)  # ✅ Callable

# Step 2: Create migration
# apps/learning/migrations/0XXX_fix_mutable_default.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('learning', '0XXX_previous_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lesson',
            name='structured_content',
            field=models.JSONField(default=list, blank=True),
        ),
    ]
```

### Option 2: Use Explicit Callable Function

**Pros**: More explicit, easier to understand for beginners
**Cons**: More verbose
**Effort**: 2 hours
**Risk**: Low

```python
def default_content():
    return []

class Lesson(models.Model):
    structured_content = models.JSONField(default=default_content, blank=True)
```

## Recommended Action

✅ **Option 1** - Use callable `default=list` (standard Django pattern)

## Technical Details

**Affected Models**:
- `apps/learning/models.py` - Lesson model
- Potentially other models with JSONField (audit needed)

**Database Changes**: Schema migration only (no data migration needed)

## Acceptance Criteria

- [ ] Update Lesson.structured_content to use `default=list` (callable)
- [ ] Create and apply migration
- [ ] Add regression test to verify separate instances
- [ ] Audit other models for same issue
- [ ] All existing tests pass

## Testing Strategy

```python
# Regression test
def test_jsonfield_mutable_default_fixed():
    """Verify JSONField default doesn't share state between instances."""
    lesson1 = Lesson.objects.create(title="Lesson 1")
    lesson2 = Lesson.objects.create(title="Lesson 2")

    # Modify lesson1's structured_content
    lesson1.structured_content.append({"type": "text", "content": "Test"})
    lesson1.save()

    # Verify lesson2 is unaffected
    lesson2.refresh_from_db()
    assert lesson2.structured_content == [], \
        f"Mutable default bug: lesson2 content is {lesson2.structured_content}"

    # Verify lesson1 has correct data
    lesson1.refresh_from_db()
    assert len(lesson1.structured_content) == 1
    assert lesson1.structured_content[0]["type"] == "text"

# Model audit
def test_no_mutable_defaults_in_models():
    """Scan all models for mutable default anti-pattern."""
    from django.apps import apps

    dangerous_patterns = []

    for model in apps.get_models():
        for field in model._meta.get_fields():
            if hasattr(field, 'default') and field.default is not None:
                # Check if default is a mutable object (not callable)
                if isinstance(field.default, (list, dict, set)):
                    dangerous_patterns.append(
                        f"{model.__name__}.{field.name} has mutable default"
                    )

    assert not dangerous_patterns, \
        f"Found mutable defaults: {dangerous_patterns}"
```

## Resources

- Django docs: https://docs.djangoproject.com/en/5.0/ref/models/fields/#default
- Common Django mistakes: https://docs.djangoproject.com/en/5.0/howto/custom-model-fields/#default-field-values

## Work Log

### 2025-10-20 - Data Integrity Review Discovery
**By:** Claude Code Review System
**Actions:**
- Discovered during data integrity guardian review
- Identified as critical data corruption risk
- Categorized as P1 (immediate fix required)

**Learnings:**
- Mutable defaults are shared across instances
- Can cause intermittent, hard-to-reproduce bugs
- Standard Django anti-pattern

## Notes

- This is a **data integrity critical** fix
- Simple to fix (2 hours)
- Low risk (standard Django migration)
- Should be completed in Phase 1 (Day 1)
- May affect other models - full audit needed
