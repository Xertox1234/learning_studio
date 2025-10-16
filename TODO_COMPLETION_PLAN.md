# TODO Items & Incomplete Features - Completion Plan
**Date:** October 14, 2025  
**Project:** Python Learning Studio  
**Purpose:** Identify and complete all unfinished features and TODOs

---

## Executive Summary

This document catalogs all incomplete features, TODO comments, and unused code found in the Python Learning Studio codebase. Each item includes context, implementation plan, priority, and estimated effort.

### Summary Statistics
- **Active TODO Items:** 8 unique items
- **Backup Files to Remove:** 1 file (`views_backup.py`)
- **Priority Breakdown:**
  - 🔴 High Priority: 3 items
  - 🟡 Medium Priority: 3 items
  - 🟢 Low Priority: 2 items

---

## 1. Active TODO Items

### 🔴 TODO #1: Create Submission Record System
**Priority:** HIGH | **Effort:** 4-6 hours | **Status:** INCOMPLETE

**Location:** `apps/api/views/code_execution.py:91`

**Current Code:**
```python
# TODO: Create submission record when ExerciseSubmission model is available
# For now, just return the result without storing submission
result['submission_id'] = None  # Placeholder
```

**Context:**
The code execution system executes user code but doesn't persist submissions. This prevents:
- Tracking user progress
- Building submission history
- Analytics on exercise attempts
- Leaderboards and achievements

**Implementation Plan:**

#### Step 1: Check if ExerciseSubmission model exists
```python
# Check apps/learning/models.py or apps/exercises/models.py
from apps.learning.models import Exercise, Submission

# Or create new model if missing
```

#### Step 2: Create ExerciseSubmission model (if missing)
```python
# apps/learning/models.py or apps/exercises/models.py

class ExerciseSubmission(models.Model):
    """
    Records of user code submissions for exercises.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='exercise_submissions'
    )
    exercise = models.ForeignKey(
        'Exercise',  # Or WagtailExercisePage
        on_delete=models.CASCADE,
        related_name='submissions'
    )
    code = models.TextField(
        help_text="User's submitted code"
    )
    
    # Execution results
    success = models.BooleanField(default=False)
    output = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    execution_time = models.FloatField(
        null=True, 
        blank=True,
        help_text="Execution time in milliseconds"
    )
    
    # Test results
    tests_passed = models.IntegerField(default=0)
    tests_total = models.IntegerField(default=0)
    score = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Score out of 100"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['exercise', '-created_at']),
            models.Index(fields=['success', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.exercise} - {self.created_at}"
    
    @property
    def pass_rate(self):
        """Calculate percentage of tests passed"""
        if self.tests_total == 0:
            return 0
        return (self.tests_passed / self.tests_total) * 100
```

#### Step 3: Update code_execution view
```python
# apps/api/views/code_execution.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@ratelimit(key='user', rate=settings.RATE_LIMIT_SETTINGS['CODE_EXECUTION'], method='POST', block=True)
def execute_exercise_code(request):
    """Execute user code for a specific exercise and save submission."""
    try:
        exercise_id = request.data.get('exercise_id')
        code = request.data.get('code', '')
        
        if not exercise_id or not code:
            return Response({
                'success': False,
                'error': 'Missing exercise_id or code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get exercise
        from apps.blog.models import WagtailExercisePage
        exercise = get_object_or_404(WagtailExercisePage, id=exercise_id)
        
        # Get test cases
        test_cases = []
        for test_block in exercise.test_cases:
            test_cases.append({
                'input': test_block.value.get('input', ''),
                'expected_output': test_block.value.get('expected_output', ''),
                'is_hidden': test_block.value.get('is_hidden', False)
            })
        
        # Execute code with test validation
        from apps.learning.code_execution import code_executor
        result = code_executor.execute_with_tests(
            code=code,
            test_cases=test_cases,
            time_limit=30,
            memory_limit=256
        )
        
        # ✅ CREATE SUBMISSION RECORD
        from apps.learning.models import ExerciseSubmission
        
        submission = ExerciseSubmission.objects.create(
            user=request.user,
            exercise=exercise,
            code=code,
            success=result.get('success', False),
            output=result.get('output', ''),
            error_message=result.get('error', ''),
            execution_time=result.get('execution_time'),
            tests_passed=result.get('tests_passed', 0),
            tests_total=result.get('tests_total', 0),
            score=result.get('score'),
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:255]
        )
        
        # Update result with submission ID
        result['submission_id'] = submission.id
        
        # Update user progress if all tests passed
        if submission.success and submission.pass_rate == 100:
            from apps.learning.models import StudentProgress
            progress, created = StudentProgress.objects.get_or_create(
                user=request.user,
                exercise=exercise
            )
            if not progress.completed:
                progress.completed = True
                progress.completed_at = timezone.now()
                progress.best_score = submission.score
                progress.save()
        
        return Response(result)
        
    except Exception as e:
        logger.error(f"Error executing exercise code: {str(e)}")
        return Response({
            'success': False,
            'error': 'Code execution failed'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

#### Step 4: Add serializer
```python
# apps/api/serializers.py

class ExerciseSubmissionSerializer(serializers.ModelSerializer):
    exercise_title = serializers.CharField(source='exercise.title', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ExerciseSubmission
        fields = [
            'id', 'user', 'user_username', 'exercise', 'exercise_title',
            'code', 'success', 'output', 'error_message', 'execution_time',
            'tests_passed', 'tests_total', 'score', 'pass_rate',
            'created_at', 'ip_address'
        ]
        read_only_fields = ['id', 'created_at', 'pass_rate']
```

#### Step 5: Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 6: Add admin interface
```python
# apps/learning/admin.py or apps/exercises/admin.py

@admin.register(ExerciseSubmission)
class ExerciseSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'exercise', 'success', 'score', 'tests_passed', 'tests_total', 'created_at']
    list_filter = ['success', 'created_at', 'exercise']
    search_fields = ['user__username', 'user__email', 'exercise__title']
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Submission Info', {
            'fields': ('user', 'exercise', 'code', 'created_at')
        }),
        ('Results', {
            'fields': ('success', 'output', 'error_message', 'execution_time')
        }),
        ('Test Results', {
            'fields': ('tests_passed', 'tests_total', 'score')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
```

**Testing Plan:**
1. Create test exercise with test cases
2. Submit code via API
3. Verify submission record created
4. Check progress update for successful submissions
5. Test failure cases

**Dependencies:**
- None (self-contained)

**Estimated Time:** 4-6 hours

---

### 🔴 TODO #2: Fix Tag Integration
**Priority:** HIGH | **Effort:** 3-4 hours | **Status:** INCOMPLETE

**Locations:**
- `apps/api/views/wagtail.py:447`
- `apps/api/views.py:2485`
- `apps/api/views.py:2635`
- `apps/api/views_backup.py` (multiple instances)

**Current Code:**
```python
'tags': []  # TODO: Fix tag integration
```

**Context:**
Tags are defined in models but not being serialized in API responses. The tag system uses Wagtail's `ClusterTaggableManager`.

**Root Cause Analysis:**
```python
# In apps/blog/models.py:
tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
```

The tags exist in the model but the serialization code returns empty array.

**Implementation Plan:**

#### Step 1: Verify tag model setup
```python
# apps/blog/models.py should have:

from taggit.models import TaggedItemBase
from modelcluster.fields import ParentalKey
from modelcluster.contrib.taggit import ClusterTaggableManager

class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        'BlogPage',
        related_name='tagged_items',
        on_delete=models.CASCADE
    )
```

#### Step 2: Update API serialization (Method 1 - Inline fix)
```python
# apps/api/views/wagtail.py:447
# Replace:
'tags': []  # TODO: Fix tag integration

# With:
'tags': [
    {'id': tag.id, 'name': tag.name, 'slug': tag.slug}
    for tag in course.tags.all()
]
```

#### Step 3: Update API serialization (Method 2 - Helper function)
```python
# apps/api/content_serializers/streamfield.py or create new utils.py

def serialize_tags(taggable_obj):
    """
    Serialize tags from a ClusterTaggableManager.
    
    Args:
        taggable_obj: Model instance with tags attribute
        
    Returns:
        List of tag dictionaries
    """
    if not hasattr(taggable_obj, 'tags'):
        return []
    
    return [
        {
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug
        }
        for tag in taggable_obj.tags.all()
    ]

# Then use in views:
from apps.api.utils import serialize_tags

'tags': serialize_tags(course)
```

#### Step 4: Update all occurrences

**File: `apps/api/views/wagtail.py`** (Line 447)
```python
# Around line 440-450
courses_data.append({
    'id': course.id,
    'title': course.title,
    'slug': course.slug,
    # ... other fields ...
    'categories': [
        {
            'name': cat.name,
            'slug': cat.slug,
            'color': cat.color
        }
        for cat in course.categories.all()
    ],
    'tags': serialize_tags(course)  # ✅ Fixed
})
```

**File: `apps/api/views.py`** (Lines 2485, 2635)
```python
# Line 2485 - Blog posts list
posts_data.append({
    # ... other fields ...
    'categories': categories,
    'tags': serialize_tags(post),  # ✅ Fixed
    'featured_image': get_featured_image_url(post),  # Also fix this TODO
    'body_preview': body_content[:2]
})

# Line 2635 - Blog post detail
return Response({
    # ... other fields ...
    'categories': categories_data,
    'tags': serialize_tags(post),  # ✅ Fixed
    # ... other fields ...
})
```

#### Step 5: Add tag filtering endpoint
```python
# apps/api/views/wagtail.py

@api_view(['GET'])
@permission_classes([AllowAny])
def get_tags(request):
    """
    Get all tags used across the site.
    Optional filtering by content type.
    """
    from taggit.models import Tag
    from django.db.models import Count
    
    content_type = request.GET.get('type')  # 'course', 'blog', 'exercise'
    
    # Get tags with usage count
    tags = Tag.objects.annotate(
        usage_count=Count('taggit_taggeditem_items')
    ).filter(usage_count__gt=0).order_by('-usage_count', 'name')
    
    # Filter by content type if specified
    if content_type == 'course':
        from apps.blog.models import WagtailCoursePage
        tags = tags.filter(
            blog_blogpagetag_items__content_object__content_type__model='wagtailcoursepage'
        ).distinct()
    elif content_type == 'blog':
        from apps.blog.models import BlogPage
        tags = tags.filter(
            blog_blogpagetag_items__content_object__content_type__model='blogpage'
        ).distinct()
    
    tags_data = [
        {
            'id': tag.id,
            'name': tag.name,
            'slug': tag.slug,
            'usage_count': tag.usage_count
        }
        for tag in tags[:50]  # Limit to top 50 tags
    ]
    
    return Response({
        'tags': tags_data,
        'count': len(tags_data)
    })

# Add to urlpatterns
path('api/v1/tags/', get_tags, name='api-tags'),
```

#### Step 6: Update frontend to display tags
```javascript
// frontend/src/components/TagList.jsx
export const TagList = ({ tags }) => {
  if (!tags || tags.length === 0) return null
  
  return (
    <div className="flex flex-wrap gap-2">
      {tags.map(tag => (
        <span 
          key={tag.id}
          className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
        >
          {tag.name}
        </span>
      ))}
    </div>
  )
}
```

**Testing Plan:**
1. Add tags to test course/blog post in admin
2. Fetch via API and verify tags appear
3. Test tag filtering endpoint
4. Verify tags display in frontend

**Estimated Time:** 3-4 hours

---

### 🔴 TODO #3: Add Featured Image URL
**Priority:** HIGH | **Effort:** 2-3 hours | **Status:** INCOMPLETE

**Locations:**
- `apps/api/views.py:2087`
- `apps/api/views.py:2215`
- `apps/api/views_backup.py` (multiple instances)

**Current Code:**
```python
'featured_image': None,  # TODO: Add image URL if exists
```

**Context:**
Models have `featured_image` ForeignKey to Wagtail Image model, but URL not serialized.

**Implementation Plan:**

#### Step 1: Create image serialization helper
```python
# apps/api/utils.py (create if doesn't exist)

from django.conf import settings

def get_image_url(image, rendition='fill-800x450'):
    """
    Get URL for a Wagtail image with optional rendition.
    
    Args:
        image: Wagtail Image instance or None
        rendition: Rendition spec (e.g., 'fill-800x450', 'width-500')
        
    Returns:
        Dictionary with image URLs or None
    """
    if not image:
        return None
    
    try:
        # Get rendition
        rendition_obj = image.get_rendition(rendition)
        
        # Build full URL
        base_url = settings.WAGTAILADMIN_BASE_URL.rstrip('/')
        
        return {
            'url': f"{base_url}{rendition_obj.url}",
            'width': rendition_obj.width,
            'height': rendition_obj.height,
            'alt': image.title,
            'original': {
                'url': f"{base_url}{image.file.url}",
                'width': image.width,
                'height': image.height
            }
        }
    except Exception as e:
        # Log error but don't crash
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Error getting image rendition: {str(e)}")
        return None

def get_featured_image_url(obj):
    """
    Get featured image URL from object.
    
    Args:
        obj: Model instance with featured_image attribute
        
    Returns:
        Image data dictionary or None
    """
    if not hasattr(obj, 'featured_image') or not obj.featured_image:
        return None
    
    return get_image_url(obj.featured_image, rendition='fill-800x450')
```

#### Step 2: Update API views
```python
# apps/api/views.py

from apps.api.utils import get_featured_image_url

# Line 2087 - Blog posts list
posts_data.append({
    # ... other fields ...
    'featured_image': get_featured_image_url(post),  # ✅ Fixed
    'body_preview': body_content[:2]
})

# Line 2215 - Related posts
related_data.append({
    # ... other fields ...
    'featured_image': get_featured_image_url(related),  # ✅ Fixed
})
```

#### Step 3: Add multiple renditions support (optional)
```python
def get_image_renditions(image, renditions=None):
    """
    Get multiple renditions of an image.
    
    Args:
        image: Wagtail Image instance
        renditions: Dict of {name: spec} or None for defaults
        
    Returns:
        Dictionary with rendition URLs
    """
    if not image:
        return None
    
    if renditions is None:
        renditions = {
            'thumbnail': 'fill-200x200',
            'small': 'fill-400x300',
            'medium': 'fill-800x450',
            'large': 'width-1200',
            'original': None  # Original image
        }
    
    result = {
        'alt': image.title,
        'renditions': {}
    }
    
    base_url = settings.WAGTAILADMIN_BASE_URL.rstrip('/')
    
    for name, spec in renditions.items():
        try:
            if spec is None:
                # Original image
                result['renditions'][name] = {
                    'url': f"{base_url}{image.file.url}",
                    'width': image.width,
                    'height': image.height
                }
            else:
                rendition = image.get_rendition(spec)
                result['renditions'][name] = {
                    'url': f"{base_url}{rendition.url}",
                    'width': rendition.width,
                    'height': rendition.height
                }
        except Exception as e:
            continue
    
    return result if result['renditions'] else None
```

#### Step 4: Update frontend components
```javascript
// frontend/src/components/FeaturedImage.jsx

export const FeaturedImage = ({ image, size = 'medium', className = '' }) => {
  if (!image || !image.url) return null
  
  return (
    <img
      src={image.url}
      alt={image.alt || ''}
      width={image.width}
      height={image.height}
      className={`object-cover ${className}`}
      loading="lazy"
    />
  )
}

// Usage in blog post cards:
<FeaturedImage image={post.featured_image} className="rounded-lg" />
```

**Testing Plan:**
1. Add featured images to test posts via admin
2. Fetch via API and verify URLs returned
3. Test images load in frontend
4. Test with missing images (should handle gracefully)

**Estimated Time:** 2-3 hours

---

### 🟡 TODO #4: Add Test Case Validation and Scoring
**Priority:** MEDIUM | **Effort:** 3-4 hours | **Status:** INCOMPLETE

**Location:** `apps/learning/views.py:229`

**Current Code:**
```python
# Execute the code
result = code_executor.execute_python_code(code)

# For now, just return execution result
# TODO: Add test case validation and scoring
return JsonResponse({
    'success': result.success,
    'output': result.output,
    'error': result.error_message if not result.success else None,
    'submission_id': 1,  # Placeholder
    'test_results': []  # Placeholder
})
```

**Context:**
This is the legacy exercise submission view. The newer `execute_exercise_code` endpoint in `apps/api/views/code_execution.py` already has test validation. This view should either:
1. Be updated to match the newer implementation, OR
2. Be deprecated in favor of the new endpoint

**Implementation Plan:**

#### Option 1: Update to match new implementation
```python
# apps/learning/views.py

@csrf_exempt
def submit_exercise(request):
    """
    LEGACY: Submit exercise solution for validation.
    NOTE: Consider using /api/v1/execute-exercise-code/ instead.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exercise_id = data.get('exercise_id')
            code = data.get('code', '')
            
            if not exercise_id or not code:
                return JsonResponse({
                    'success': False,
                    'error': 'Missing exercise_id or code'
                }, status=400)
            
            # Get exercise
            exercise = Exercise.objects.get(id=exercise_id)
            
            # Get test cases
            test_cases = list(exercise.test_cases.all().values(
                'input_data', 'expected_output', 'is_hidden'
            ))
            
            # Execute with test validation
            from apps.learning.code_execution import code_executor
            result = code_executor.execute_with_tests(
                code=code,
                test_cases=[
                    {
                        'input': tc['input_data'],
                        'expected_output': tc['expected_output'],
                        'is_hidden': tc['is_hidden']
                    }
                    for tc in test_cases
                ],
                time_limit=30,
                memory_limit=256
            )
            
            # Create submission if user authenticated
            submission_id = None
            if request.user.is_authenticated:
                from apps.learning.models import ExerciseSubmission
                submission = ExerciseSubmission.objects.create(
                    user=request.user,
                    exercise=exercise,
                    code=code,
                    success=result.get('success', False),
                    output=result.get('output', ''),
                    error_message=result.get('error', ''),
                    tests_passed=result.get('tests_passed', 0),
                    tests_total=result.get('tests_total', 0),
                    score=result.get('score')
                )
                submission_id = submission.id
            
            return JsonResponse({
                'success': result.get('success', False),
                'output': result.get('output', ''),
                'error': result.get('error'),
                'submission_id': submission_id,
                'test_results': result.get('test_results', []),
                'tests_passed': result.get('tests_passed', 0),
                'tests_total': result.get('tests_total', 0),
                'score': result.get('score')
            })
            
        except Exercise.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Exercise not found'
            }, status=404)
        except Exception as e:
            logger.error(f"Error submitting exercise: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Submission failed'
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    }, status=405)
```

#### Option 2: Deprecate and redirect (Recommended)
```python
# apps/learning/views.py

@csrf_exempt
def submit_exercise(request):
    """
    DEPRECATED: This endpoint is deprecated.
    Please use /api/v1/execute-exercise-code/ instead.
    
    This legacy endpoint is maintained for backward compatibility
    but will be removed in a future version.
    """
    return JsonResponse({
        'success': False,
        'error': 'This endpoint is deprecated. Please use /api/v1/execute-exercise-code/',
        'deprecated': True,
        'new_endpoint': '/api/v1/execute-exercise-code/'
    }, status=410)  # 410 Gone
```

**Recommendation:** Use Option 2 (deprecate) to avoid maintaining duplicate code.

**Estimated Time:** 1-2 hours

---

### 🟡 TODO #5: Update Progress via API
**Priority:** MEDIUM | **Effort:** 2-3 hours | **Status:** INCOMPLETE

**Location:** `frontend/src/pages/WagtailLessonPage.jsx:485`

**Current Code:**
```javascript
const handleMarkComplete = () => {
  setCompleted(true)
  // TODO: Update progress via API
}
```

**Context:**
The "Mark as Complete" button updates local state but doesn't persist to backend.

**Implementation Plan:**

#### Step 1: Create progress tracking API endpoint
```python
# apps/api/views/wagtail.py

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_lesson_complete(request, lesson_id):
    """
    Mark a lesson as completed for the current user.
    """
    from apps.blog.models import WagtailLessonPage, LessonProgress
    
    try:
        lesson = get_object_or_404(WagtailLessonPage, id=lesson_id)
        
        # Create or update progress
        progress, created = LessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={
                'completed': True,
                'completed_at': timezone.now(),
                'last_accessed': timezone.now()
            }
        )
        
        # Update course progress
        if lesson.get_parent().specific_class == WagtailCoursePage:
            course = lesson.get_parent().specific
            update_course_progress(request.user, course)
        
        return Response({
            'success': True,
            'progress': {
                'lesson_id': lesson.id,
                'completed': progress.completed,
                'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
                'progress_percentage': calculate_lesson_progress(request.user, lesson)
            }
        })
        
    except Exception as e:
        logger.error(f"Error marking lesson complete: {str(e)}")
        return Response({
            'success': False,
            'error': 'Failed to update progress'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def update_course_progress(user, course):
    """Update overall course progress for user."""
    from apps.blog.models import CourseProgress
    
    # Get all lessons in course
    lessons = course.get_children().type(WagtailLessonPage)
    total_lessons = lessons.count()
    
    if total_lessons == 0:
        return
    
    # Count completed lessons
    completed_lessons = LessonProgress.objects.filter(
        user=user,
        lesson__in=lessons,
        completed=True
    ).count()
    
    # Calculate percentage
    progress_percentage = (completed_lessons / total_lessons) * 100
    
    # Update course progress
    course_progress, created = CourseProgress.objects.update_or_create(
        user=user,
        course=course,
        defaults={
            'progress_percentage': progress_percentage,
            'lessons_completed': completed_lessons,
            'last_accessed': timezone.now()
        }
    )
    
    # Mark course as completed if 100%
    if progress_percentage >= 100 and not course_progress.completed:
        course_progress.completed = True
        course_progress.completed_at = timezone.now()
        course_progress.save()

# Add to URLs
path('api/v1/lessons/<int:lesson_id>/complete/', mark_lesson_complete, name='mark-lesson-complete'),
```

#### Step 2: Create models if missing
```python
# apps/blog/models.py or apps/learning/models.py

class LessonProgress(models.Model):
    """Track user progress through lessons."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lesson_progress'
    )
    lesson = models.ForeignKey(
        'blog.WagtailLessonPage',
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.IntegerField(
        default=0,
        help_text="Time spent in seconds"
    )
    
    class Meta:
        unique_together = ['user', 'lesson']
        ordering = ['-last_accessed']
        indexes = [
            models.Index(fields=['user', 'completed']),
            models.Index(fields=['lesson', 'completed']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"

class CourseProgress(models.Model):
    """Track user progress through courses."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='course_progress'
    )
    course = models.ForeignKey(
        'blog.WagtailCoursePage',
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    progress_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    lessons_completed = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-last_accessed']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.progress_percentage}%)"
```

#### Step 3: Update frontend
```javascript
// frontend/src/pages/WagtailLessonPage.jsx

const handleMarkComplete = async () => {
  try {
    const response = await axios.post(
      `/api/v1/lessons/${lesson.id}/complete/`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    )
    
    if (response.data.success) {
      setCompleted(true)
      
      // Show success message
      toast.success('Lesson marked as complete!', {
        description: `Progress: ${response.data.progress.progress_percentage}%`
      })
      
      // Optionally update parent course progress
      if (response.data.course_progress) {
        // Update course progress indicator
      }
    }
  } catch (error) {
    console.error('Error marking lesson complete:', error)
    toast.error('Failed to update progress', {
      description: 'Please try again'
    })
  }
}
```

#### Step 4: Add progress indicators
```javascript
// frontend/src/components/LessonProgressBar.jsx

export const LessonProgressBar = ({ courseId }) => {
  const [progress, setProgress] = useState(null)
  
  useEffect(() => {
    fetchProgress()
  }, [courseId])
  
  const fetchProgress = async () => {
    try {
      const response = await axios.get(`/api/v1/courses/${courseId}/progress/`)
      setProgress(response.data)
    } catch (error) {
      console.error('Error fetching progress:', error)
    }
  }
  
  if (!progress) return null
  
  return (
    <div className="w-full">
      <div className="flex justify-between text-sm mb-2">
        <span>Course Progress</span>
        <span>{progress.progress_percentage}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div 
          className="bg-blue-600 h-2 rounded-full transition-all"
          style={{ width: `${progress.progress_percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-600 mt-1">
        {progress.lessons_completed} of {progress.total_lessons} lessons completed
      </p>
    </div>
  )
}
```

**Testing Plan:**
1. Mark lesson as complete
2. Verify progress saved to database
3. Check course progress updates
4. Test progress persistence across sessions

**Estimated Time:** 2-3 hours

---

## 2. Unused Code & Files to Remove

### 🔴 Remove Backup File
**Priority:** HIGH | **Effort:** 5 minutes | **Status:** TO DELETE

**File:** `apps/api/views_backup.py`

**Analysis:**
- 3,239 lines of code
- Exact duplicate of `apps/api/views.py`
- Contains same TODO items
- No references found in codebase

**Action Plan:**
```bash
# 1. Verify no imports reference it
grep -r "views_backup" apps/
grep -r "from.*views_backup" apps/

# 2. Check git history to confirm it's a backup
git log --follow apps/api/views_backup.py

# 3. Remove the file
git rm apps/api/views_backup.py
git commit -m "Remove redundant backup file views_backup.py"
```

**Risk:** LOW - No code references found

---

## 3. Code Quality Improvements

### 🟢 Placeholder Function Names
**Priority:** LOW | **Effort:** 30 minutes | **Status:** COSMETIC

**Locations:**
- Multiple template files use `def TODO(numbers):` as placeholder
- These are intentional placeholder examples for students

**Examples:**
- `templates/test-editor.html:34`
- `templates/learning/exercise_interface.html` (multiple)
- `templates/simple-test.html:79`
- `static/js/*` (multiple)

**Context:**
These are **intentional placeholders** for exercise starter code. They should be:
1. Left as-is if they're examples, OR
2. Made more descriptive like `def find_max(numbers):`

**Recommendation:** Leave as-is - these are teaching examples

---

### 🟢 Streamfield Content Truncation
**Priority:** LOW | **Effort:** N/A | **Status:** NOT A PROBLEM

**Locations:**
- Multiple instances of `[:200] + '...'` for content preview
- This is intentional truncation for previews

**Example:**
```python
'content': str(post.content)[:200] + '...' if len(str(post.content)) > 200 else str(post.content)
```

**Recommendation:** This is working as intended - provides previews

---

## 4. Implementation Priority Order

### Phase 1: Critical TODOs (Week 1)
1. ✅ **Remove views_backup.py** (5 minutes)
2. 🔧 **Fix Tag Integration** (3-4 hours)
3. 🔧 **Add Featured Image URLs** (2-3 hours)
4. 🔧 **Create Submission Record System** (4-6 hours)

**Total Time:** ~10-14 hours (2 days)

### Phase 2: Progress Tracking (Week 2)
5. 🔧 **Update Progress via API** (2-3 hours)
6. 🔧 **Add Test Case Validation** (1-2 hours via deprecation)

**Total Time:** ~3-5 hours (1 day)

### Phase 3: Enhancement (Week 3)
7. Add comprehensive tests for new features
8. Update documentation
9. Add admin interfaces
10. Create migration guide for deprecated endpoints

---

## 5. Testing Strategy

### Unit Tests Template
```python
# apps/learning/tests/test_submissions.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.learning.models import Exercise, ExerciseSubmission
from apps.blog.models import WagtailExercisePage

User = get_user_model()

class ExerciseSubmissionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        # Create test exercise
        
    def test_create_submission(self):
        """Test creating an exercise submission."""
        # Test implementation
        
    def test_calculate_score(self):
        """Test score calculation."""
        # Test implementation
        
    def test_update_progress(self):
        """Test progress update on successful submission."""
        # Test implementation
```

### Integration Tests
```python
# apps/api/tests/test_exercise_api.py

from rest_framework.test import APITestCase
from rest_framework import status

class ExerciseAPITests(APITestCase):
    def test_execute_with_submission(self):
        """Test code execution creates submission record."""
        # Test implementation
        
    def test_tag_serialization(self):
        """Test tags appear in API response."""
        # Test implementation
        
    def test_featured_image_url(self):
        """Test featured image URL generation."""
        # Test implementation
```

---

## 6. Migration Plan

### Step-by-Step Execution

#### Day 1: Cleanup & Setup
```bash
# 1. Create feature branch
git checkout -b feature/complete-todos

# 2. Remove backup file
git rm apps/api/views_backup.py

# 3. Create models
# - Edit apps/learning/models.py
# - Add ExerciseSubmission model
# - Add LessonProgress model  
# - Add CourseProgress model

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Commit
git add .
git commit -m "Add progress tracking models and remove backup file"
```

#### Day 2: Fix API Serialization
```bash
# 1. Create utils file
# - Create apps/api/utils.py
# - Add get_featured_image_url()
# - Add serialize_tags()

# 2. Update views
# - Fix apps/api/views/wagtail.py (tags)
# - Fix apps/api/views.py (tags + images)

# 3. Test changes
python manage.py test apps.api

# 4. Commit
git add .
git commit -m "Fix tag integration and featured image URLs"
```

#### Day 3: Submission System
```bash
# 1. Update code_execution.py
# - Implement submission creation
# - Add progress tracking

# 2. Add serializers

# 3. Update admin

# 4. Test
python manage.py test apps.learning

# 5. Commit
git add .
git commit -m "Implement exercise submission tracking system"
```

#### Day 4: Frontend Progress Tracking
```bash
# 1. Create progress API endpoints

# 2. Update frontend components

# 3. Test end-to-end

# 4. Commit
git add .
git commit -m "Add lesson progress tracking with API integration"
```

#### Day 5: Deprecation & Documentation
```bash
# 1. Deprecate old endpoint

# 2. Update documentation

# 3. Add tests

# 4. Final commit
git add .
git commit -m "Deprecate legacy endpoint and update documentation"

# 5. Create PR
git push origin feature/complete-todos
```

---

## 7. Success Criteria

### Completion Checklist
- [ ] All backup files removed
- [ ] Tags appear in all API responses
- [ ] Featured images have URLs in responses
- [ ] Exercise submissions saved to database
- [ ] Lesson progress tracked and persisted
- [ ] Course progress calculated automatically
- [ ] All TODOs removed from codebase
- [ ] Tests pass for new features
- [ ] Admin interfaces added
- [ ] Documentation updated
- [ ] Frontend displays new data

### Performance Targets
- API response time < 200ms (unchanged)
- Database queries optimized (use select_related)
- No N+1 query issues
- Image renditions cached

### Quality Targets
- Test coverage > 80% for new code
- No linting errors
- Type hints added (Python 3.11+)
- API documentation updated

---

## 8. Risk Assessment

### High Risk Items
1. **Database Migrations** - Test in development first
   - Mitigation: Backup database before migrations
   
2. **Breaking API Changes** - Existing integrations may break
   - Mitigation: Maintain backward compatibility, deprecate gradually

### Medium Risk Items
1. **Performance Impact** - Additional queries for tags/images
   - Mitigation: Use select_related/prefetch_related, cache results
   
2. **Image Storage** - Large image files
   - Mitigation: Use CDN, implement lazy loading

### Low Risk Items
1. **Frontend Changes** - Progressive enhancement
2. **Admin Interface** - Isolated changes

---

## Conclusion

This plan addresses all incomplete features and TODOs systematically. The implementation is structured in phases to minimize risk and allows for iterative testing. 

**Estimated Total Time:** 15-20 hours (3-4 working days)

**Recommended Approach:** 
1. Start with cleanup (remove backup file)
2. Fix API serialization (tags + images) - visible improvement
3. Add submission tracking - critical feature
4. Complete progress tracking - user engagement
5. Deprecate legacy endpoints - technical debt

All TODOs can be completed within a one-week sprint with proper testing and documentation.

---

**Report Generated:** October 14, 2025  
**Next Review:** After completion of Phase 1  
**Status:** READY FOR IMPLEMENTATION
