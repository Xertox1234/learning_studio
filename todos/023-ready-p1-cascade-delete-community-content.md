---
status: ready
priority: p1
issue_id: "023"
tags: [data-integrity, gdpr, community, high-risk]
dependencies: [024]
---

# Fix CASCADE Deletes Destroying Community Content

## Problem Statement

90 CASCADE delete relationships will destroy all community content (posts, topics, discussions, reviews) when a user account is deleted. This causes irreversible loss of valuable community contributions and breaks conversation threads.

**Category**: Data Integrity / Business Risk
**Severity**: Critical (P1)
**Impact**: Community content loss, broken discussions, GDPR compliance issues

## Findings

**Discovered during**: Data integrity review (2025-10-20)

**Affected Models** (90 CASCADE relationships):
```python
# ❌ User deletion destroys ALL community contributions

# Forum content
class Post(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    # If user deleted → ALL their posts deleted

class Topic(models.Model):
    poster = models.ForeignKey(User, on_delete=models.CASCADE)
    # If user deleted → ALL their topics deleted

# Learning content
class Discussion(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # If user deleted → ALL discussions deleted

class CourseReview(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    # If user deleted → ALL reviews deleted

class PeerReview(models.Model):
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    # If user deleted → ALL peer reviews deleted

# And 85 more CASCADE relationships...
```

**Impact Scenarios**:

1. **Valuable contributor leaves**:
   - User with 1,000 helpful forum posts deletes account
   - ALL 1,000 posts vanish
   - Conversation threads broken (orphaned replies)
   - Knowledge base destroyed

2. **GDPR "right to be forgotten"**:
   - EU user requests account deletion
   - Must delete PII (name, email, personal data)
   - But should preserve community contributions
   - Current implementation deletes everything

3. **Spam/abuse account ban**:
   - Moderator bans spam account
   - Deleting account removes evidence
   - Cannot audit what was deleted

## Proposed Solutions

### Option 1: SET_NULL with Cached Username (RECOMMENDED)

**Pros**:
- Preserves community content
- GDPR compliant (anonymizes PII)
- Maintains conversation continuity
- Allows content moderation history
- Minimal code changes

**Cons**:
- Requires data migration
- Adds username cache field

**Effort**: 8-12 hours
**Risk**: Medium (high-impact data migration)

**Implementation**:
```python
# File: apps/forum_integration/models.py

class Post(models.Model):
    # ✅ Change CASCADE to SET_NULL
    poster = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='forum_posts'
    )

    # ✅ Cache username for display (survives user deletion)
    poster_username = models.CharField(max_length=150, db_index=True)

    def save(self, *args, **kwargs):
        # Cache username on creation
        if self.poster and not self.poster_username:
            self.poster_username = self.poster.username
        super().save(*args, **kwargs)

    @property
    def author_display(self):
        """Display name for template rendering."""
        if self.poster:
            return self.poster.username
        return self.poster_username or "[deleted]"

class Topic(models.Model):
    # Same pattern
    poster = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    poster_username = models.CharField(max_length=150)

# File: apps/learning/models.py
class Discussion(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    author_name = models.CharField(max_length=150)

class CourseReview(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    author_name = models.CharField(max_length=150)
```

**Data Migration**:
```python
# apps/forum_integration/migrations/0XXX_change_cascade_to_set_null.py

def populate_cached_usernames(apps, schema_editor):
    """Populate username caches before changing foreign key."""
    Post = apps.get_model('forum_integration', 'Post')
    Topic = apps.get_model('forum_integration', 'Topic')

    # Batch update to avoid memory issues
    batch_size = 1000

    for model in [Post, Topic]:
        total = model.objects.count()
        print(f"Processing {total} {model.__name__} records...")

        for i in range(0, total, batch_size):
            batch = model.objects.select_related('poster')[i:i+batch_size]
            updates = []

            for obj in batch:
                if obj.poster:
                    obj.poster_username = obj.poster.username
                    updates.append(obj)

            if updates:
                model.objects.bulk_update(updates, ['poster_username'])

        print(f"✓ {model.__name__} complete")

class Migration(migrations.Migration):
    dependencies = [
        ('forum_integration', '0XXX_previous'),
        ('users', '0XXX_soft_delete'),  # Requires soft delete infrastructure
    ]

    operations = [
        # Step 1: Add cached username fields
        migrations.AddField(
            model_name='post',
            name='poster_username',
            field=models.CharField(max_length=150, default='', db_index=True),
        ),
        migrations.AddField(
            model_name='topic',
            name='poster_username',
            field=models.CharField(max_length=150, default=''),
        ),

        # Step 2: Populate cached usernames from existing data
        migrations.RunPython(
            populate_cached_usernames,
            reverse_code=migrations.RunPython.noop
        ),

        # Step 3: Change foreign key to SET_NULL
        migrations.AlterField(
            model_name='post',
            name='poster',
            field=models.ForeignKey(
                'users.User',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='forum_posts'
            ),
        ),
        migrations.AlterField(
            model_name='topic',
            name='poster',
            field=models.ForeignKey(
                'users.User',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='forum_topics'
            ),
        ),
    ]
```

### Option 2: Transfer to System User

**Pros**: Maintains foreign key integrity
**Cons**: Misleading attribution, requires system account

```python
# Less recommended
DELETED_USER_ID = 1  # System "deleted" account

class Post(models.Model):
    poster = models.ForeignKey(
        User,
        on_delete=models.SET(lambda: User.objects.get(id=DELETED_USER_ID))
    )
```

## Recommended Action

✅ **Option 1** - SET_NULL with cached username (GDPR compliant, preserves content)

**CRITICAL DEPENDENCY**: Requires soft delete infrastructure (Todo #024) to be implemented first

## Technical Details

**Affected Files** (90 models across 4 apps):
- `apps/forum_integration/models.py` - Post, Topic (30 relationships)
- `apps/learning/models.py` - Discussion, Review (25 relationships)
- `apps/community/models.py` - PeerReview, CodeReview (20 relationships)
- `apps/users/models.py` - UserActivity (15 relationships)

**Database Changes**:
- Add username cache fields (90 fields)
- Change on_delete from CASCADE to SET_NULL
- Data migration to populate caches

**GDPR Compliance**:
✅ Preserves community value
✅ Anonymizes PII (user FK set to NULL)
✅ Displays cached username (not personal data)
✅ Allows "right to be forgotten"

## Acceptance Criteria

- [ ] Soft delete infrastructure implemented (Todo #024)
- [ ] Add username cache fields to all 90 models
- [ ] Create data migration to populate caches
- [ ] Change CASCADE to SET_NULL for all 90 relationships
- [ ] Update serializers to use author_display property
- [ ] Test user deletion preserves content
- [ ] Test orphaned content displays correctly
- [ ] All tests pass
- [ ] GDPR compliance verified

## Testing Strategy

```python
def test_user_deletion_preserves_community_content():
    """Deleting user should preserve their posts/topics."""
    user = User.objects.create(username='testuser')

    # User creates content
    post = Post.objects.create(
        poster=user,
        poster_username=user.username,
        content='Valuable contribution'
    )
    topic = Topic.objects.create(
        poster=user,
        poster_username=user.username,
        subject='Important discussion'
    )

    post_id = post.id
    topic_id = topic.id

    # User account deleted
    user.delete()

    # ✅ Content still exists
    post = Post.objects.get(id=post_id)
    topic = Topic.objects.get(id=topic_id)

    # ✅ FK is NULL
    assert post.poster is None
    assert topic.poster is None

    # ✅ Cached username preserved
    assert post.poster_username == 'testuser'
    assert topic.poster_username == 'testuser'

    # ✅ Display name shows cached username
    assert post.author_display == 'testuser'

def test_gdpr_anonymization():
    """GDPR deletion removes PII but keeps content."""
    user = User.objects.create(
        username='john_doe',
        email='john@example.com',
        first_name='John',
        last_name='Doe'
    )

    post = Post.objects.create(
        poster=user,
        poster_username=user.username,
        content='My opinion on topic'
    )

    # GDPR "right to be forgotten"
    user.soft_delete(reason='GDPR request')
    user.anonymize_personal_data()

    # ✅ PII removed
    user.refresh_from_db()
    assert user.first_name == ''
    assert user.last_name == ''
    assert 'deleted_user_' in user.username
    assert '@deleted.local' in user.email

    # ✅ Content preserved
    post.refresh_from_db()
    assert post.content == 'My opinion on topic'

    # ✅ Original username still shown
    assert post.author_display == 'john_doe'

def test_conversation_continuity():
    """Deleting post author doesn't break conversation thread."""
    author = User.objects.create(username='author')
    replier = User.objects.create(username='replier')

    topic = Topic.objects.create(
        poster=author,
        poster_username='author',
        subject='Question'
    )

    post1 = Post.objects.create(
        topic=topic,
        poster=author,
        poster_username='author',
        content='Original question'
    )

    post2 = Post.objects.create(
        topic=topic,
        poster=replier,
        poster_username='replier',
        content='Helpful answer'
    )

    # Author deletes account
    author.delete()

    # ✅ Topic still exists
    topic.refresh_from_db()
    assert topic.subject == 'Question'

    # ✅ Original post still exists
    post1.refresh_from_db()
    assert post1.content == 'Original question'
    assert post1.author_display == 'author'

    # ✅ Reply still exists
    post2.refresh_from_db()
    assert post2.content == 'Helpful answer'
```

## Resources

- Django on_delete options: https://docs.djangoproject.com/en/5.0/ref/models/fields/#django.db.models.ForeignKey.on_delete
- GDPR compliance: https://gdpr.eu/right-to-be-forgotten/
- Data migration guide: https://docs.djangoproject.com/en/5.0/topics/migrations/#data-migrations

## Work Log

### 2025-10-20 - Data Integrity Review Discovery
**By:** Claude Code Data Integrity Guardian
**Actions:**
- Discovered 90 CASCADE delete relationships
- Identified community content loss risk
- Analyzed GDPR compliance requirements
- Categorized as P1 (high business impact)

**Learnings:**
- CASCADE deletes appropriate for truly dependent data only
- Community content should survive account deletion
- Cached denormalization enables GDPR + UX balance

## Notes

- This is a **data integrity critical** fix
- **High business impact** - affects community value
- High complexity (8-12 hours, 90 models)
- Medium risk (large data migration)
- **DEPENDS ON**: Todo #024 (soft delete infrastructure)
- Should be completed in Phase 2 (Days 3-4)
- Requires thorough testing on staging with production data copy
- Consider phased rollout (forum first, then learning content)
