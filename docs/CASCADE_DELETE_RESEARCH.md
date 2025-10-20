# CASCADE Delete Research - django-machina Model Swapping

**Date:** October 20, 2025
**Status:** Research Complete ✅
**Risk:** High (requires custom model override)
**Effort:** 4-6 hours implementation
**Priority:** P1 (data integrity)

---

## Executive Summary

Successfully researched django-machina's model swapping system. **Solution is feasible** but requires careful implementation of custom Post and Topic models to change CASCADE to SET_NULL behavior while preserving username display.

**Key Finding:** Django-machina already has a `username` field on both Post and Topic models that can cache the username for display after user deletion.

---

## Problem Statement

When a user account is deleted (soft delete), django-machina's Post and Topic models use `on_delete=models.CASCADE` which would delete all forum content. This violates GDPR requirements and community preservation goals.

**Current Behavior:**
```python
# AbstractTopic (line 34-36)
poster = models.ForeignKey(
    settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE
)

# AbstractPost (line 225-228)
poster = models.ForeignKey(
    settings.AUTH_USER_MODEL, related_name='posts',
    blank=True, null=True, on_delete=models.CASCADE
)
```

**Desired Behavior:**
- Change `on_delete=models.CASCADE` → `on_delete=models.SET_NULL`
- Preserve forum content when user deletes account
- Display cached username even when poster FK is NULL

---

## Research Findings

### 1. Django-Machina Model Swapping System

Django-machina uses a dynamic class-loading system (inspired by django-oscar) that allows complete model override.

**Documentation:** https://django-machina.readthedocs.io/en/stable/customization/recipes/overriding_models.html

**Key Steps:**
1. Create custom app with same label as django-machina app
2. Subclass abstract models (AbstractTopic, AbstractPost)
3. Import django-machina models **after** custom models
4. Generate migrations

**Critical Import Order:**
```python
# Custom models FIRST
class Topic(AbstractTopic):
    ...

# Django-machina imports LAST
from machina.apps.forum_conversation.models import *  # noqa
```

### 2. Existing Username Caching Fields

**IMPORTANT DISCOVERY:** Both models already have username caching!

**AbstractPost** (line 246):
```python
username = models.CharField(max_length=155, blank=True, null=True, verbose_name=_('Username'))
```

**AbstractTopic** (line 41):
```python
subject = models.CharField(max_length=255, verbose_name=_('Subject'))
# Note: Topic doesn't have username field, but Post does
```

**Implication:** We can use the existing `username` field for Post models. For Topic models, we need to track the poster's username separately.

### 3. Current Usage in Codebase

Checked `/Users/williamtower/projects/learning_studio/apps/forum_integration/`:

**PostEditHistory model** (already correctly using SET_NULL):
```python
edited_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,  # ✅ Already correct!
    null=True,
    blank=True
)
```

**Serializers** (apps/api/serializers/forum.py):
- PostSerializer uses `poster.username` for display
- TopicSerializer uses `poster.username` for display
- Need to update to fallback to cached `username` field

---

## Proposed Solution

### Option 1: Custom Model Override (RECOMMENDED)

**Pros:**
- Complete control over CASCADE behavior
- Standard django-machina pattern
- Preserves all forum content
- Clean migration path

**Cons:**
- Requires model swapping setup
- Need to test thoroughly
- Migration complexity

**Effort:** 4-6 hours
**Risk:** Medium (well-documented pattern, but requires testing)

**Implementation Steps:**

#### Step 1: Create Custom Forum Conversation App

```bash
# Create custom app structure
apps/forum_conversation/
├── __init__.py
├── apps.py
├── models.py
└── migrations/
    └── (copy from venv/machina/apps/forum_conversation/migrations/)
```

#### Step 2: Define Custom Models

```python
# apps/forum_conversation/models.py

from django.conf import settings
from django.db import models
from machina.apps.forum_conversation.abstract_models import AbstractTopic, AbstractPost


class Topic(AbstractTopic):
    """
    Custom Topic model with SET_NULL for poster preservation.

    Changes from base:
    - poster: on_delete=CASCADE → on_delete=SET_NULL
    - Add poster_username field to cache username
    """
    # Override poster field
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # ✅ Changed from CASCADE
        verbose_name='Poster',
    )

    # Add cached username field
    poster_username = models.CharField(
        max_length=155,
        blank=True,
        null=True,
        verbose_name='Poster Username (cached)',
        help_text='Cached username for display when poster is deleted'
    )


class Post(AbstractPost):
    """
    Custom Post model with SET_NULL for poster preservation.

    Changes from base:
    - poster: on_delete=CASCADE → on_delete=SET_NULL
    - username field already exists for caching
    """
    # Override poster field
    poster = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='posts',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # ✅ Changed from CASCADE
        verbose_name='Poster',
    )

    # Note: username field inherited from AbstractPost already handles caching


# Import machina models LAST
from machina.apps.forum_conversation.models import *  # noqa
```

#### Step 3: Update apps.py

```python
# apps/forum_conversation/apps.py

from machina.apps.forum_conversation.apps import ForumConversationAppConfig as BaseForumConversationAppConfig


class ForumConversationAppConfig(BaseForumConversationAppConfig):
    name = 'apps.forum_conversation'
    label = 'forum_conversation'  # Same label as machina app
```

#### Step 4: Update settings.py

```python
# learning_community/settings/base.py

INSTALLED_APPS = [
    # ... other apps ...

    # Replace machina's forum_conversation with our custom one
    'apps.forum_conversation',  # BEFORE machina apps

    # ... machina apps (but not forum_conversation) ...
]
```

#### Step 5: Create Signal to Cache Username

```python
# apps/forum_conversation/signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Topic, Post


@receiver(pre_save, sender=Topic)
def cache_topic_poster_username(sender, instance, **kwargs):
    """Cache poster username before saving Topic."""
    if instance.poster and not instance.poster_username:
        instance.poster_username = instance.poster.username


@receiver(pre_save, sender=Post)
def cache_post_poster_username(sender, instance, **kwargs):
    """Cache poster username before saving Post."""
    if instance.poster and not instance.username:
        instance.username = instance.poster.username
```

#### Step 6: Data Migration to Populate Cached Usernames

```python
# apps/forum_conversation/migrations/XXXX_populate_cached_usernames.py

from django.db import migrations


def populate_cached_usernames(apps, schema_editor):
    """Populate cached username fields from existing poster relationships."""
    Topic = apps.get_model('forum_conversation', 'Topic')
    Post = apps.get_model('forum_conversation', 'Post')

    # Populate Topic poster_username
    topics = Topic.objects.filter(poster__isnull=False, poster_username__isnull=True)
    for topic in topics:
        topic.poster_username = topic.poster.username
        topic.save(update_fields=['poster_username'])

    # Populate Post username
    posts = Post.objects.filter(poster__isnull=False, username__isnull=True)
    for post in posts:
        post.username = post.poster.username
        post.save(update_fields=['username'])


class Migration(migrations.Migration):
    dependencies = [
        ('forum_conversation', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.RunPython(populate_cached_usernames),
    ]
```

#### Step 7: Update Serializers

```python
# apps/api/serializers/forum.py

class TopicSerializer(serializers.ModelSerializer):
    poster_display_name = serializers.SerializerMethodField()

    def get_poster_display_name(self, obj):
        """Return poster username with fallback to cached value."""
        if obj.poster:
            return obj.poster.username
        elif obj.poster_username:
            return obj.poster_username  # Deleted user
        return 'Anonymous'


class PostSerializer(serializers.ModelSerializer):
    poster_display_name = serializers.SerializerMethodField()

    def get_poster_display_name(self, obj):
        """Return poster username with fallback to cached value."""
        if obj.poster:
            return obj.poster.username
        elif obj.username:
            return obj.username  # Deleted user or anonymous
        return 'Anonymous'
```

---

## Testing Strategy

### Test 1: User Deletion Preserves Content
```python
def test_user_deletion_preserves_forum_content():
    """Verify topic and post survive user deletion."""
    user = User.objects.create(username='testuser')
    topic = Topic.objects.create(poster=user, subject='Test')
    post = Post.objects.create(poster=user, topic=topic, subject='Test')

    # Soft delete user
    user.soft_delete()

    # Refresh from DB
    topic.refresh_from_db()
    post.refresh_from_db()

    # Verify content preserved
    assert topic.id is not None
    assert post.id is not None
    assert topic.poster is None  # FK set to NULL
    assert post.poster is None

    # Verify username cached
    assert topic.poster_username == 'testuser'
    assert post.username == 'testuser'
```

### Test 2: Serializer Fallback
```python
def test_serializer_displays_cached_username():
    """Verify serializer shows cached username for deleted users."""
    user = User.objects.create(username='testuser')
    topic = Topic.objects.create(poster=user, subject='Test')

    user.soft_delete()
    topic.refresh_from_db()

    serializer = TopicSerializer(topic)
    assert serializer.data['poster_display_name'] == 'testuser'
```

---

## Migration Plan

### Phase 1: Pre-Migration (2 hours)
1. Create custom forum_conversation app structure
2. Copy migrations from django-machina
3. Define custom Topic and Post models
4. Create signal handlers
5. Update settings.py

### Phase 2: Migration Generation (1 hour)
1. Run `makemigrations forum_conversation`
2. Review generated migration
3. Create data migration for username caching
4. Test migration on development database

### Phase 3: Testing (2 hours)
1. Run comprehensive tests
2. Test user deletion flow
3. Verify forum content preservation
4. Test serializer fallback

### Phase 4: Deployment (1 hour)
1. Deploy to staging
2. Run migrations
3. Verify forum functionality
4. Monitor for issues

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Migration breaks forum | High | Medium | Test thoroughly on staging first |
| Username caching fails | Medium | Low | Data migration handles existing content |
| Signal doesn't fire | Medium | Low | Add tests for signal behavior |
| Import order issues | High | Low | Follow django-machina docs exactly |

---

## Acceptance Criteria

- [ ] Custom Topic model created with SET_NULL
- [ ] Custom Post model created with SET_NULL
- [ ] Username caching signals implemented
- [ ] Data migration populates cached usernames
- [ ] Serializers updated with fallback logic
- [ ] Tests verify content preservation
- [ ] All existing tests pass
- [ ] Migration tested on staging

---

## Resources

- Django-machina docs: https://django-machina.readthedocs.io/en/stable/customization/recipes/overriding_models.html
- Django CASCADE to SET_NULL: https://docs.djangoproject.com/en/5.0/ref/models/fields/#django.db.models.ForeignKey.on_delete
- Model swapping mechanisms: https://django-machina.readthedocs.io/en/stable/customization/underlying_mechanisms.html

---

## Conclusion

**Status:** ✅ Research Complete - Solution Identified

**Recommendation:** Proceed with Option 1 (Custom Model Override)

**Next Steps:**
1. Create custom forum_conversation app
2. Implement custom models with SET_NULL
3. Create username caching signals
4. Test thoroughly before deployment

**Estimated Total Time:** 4-6 hours
**Risk Level:** Medium (manageable with proper testing)
**GDPR Compliance:** ✅ Will be achieved

---

**Created:** October 20, 2025
**Completed:** October 20, 2025
**Confidence:** High (django-machina pattern is well-documented)
