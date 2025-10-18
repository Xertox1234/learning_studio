# CLAUDE.md

## Development Workflow

After completing ANY coding task, you MUST:

1. **Automatically invoke the code-review-specialist sub-agent** to review changes
2. Wait for the review to complete
3. Address any blockers identified
4. Only then consider the task complete

### Code Review Process

- The code-review-specialist agent reviews ALL modified files
- Reviews check for: debug code, security issues, accessibility, testing, best practices
- ALL BLOCKERS must be fixed before proceeding
- This is NON-NEGOTIABLE for production code

### Standard Task Pattern
```
1. Plan the implementation
2. Write the code
3. **USE code-review-specialist agent to review** ← ALWAYS DO THIS
4. Fix any issues found
5. Confirm task complete
```

**Important**: Never skip the code review step. It is part of "done".

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview


Python Learning Studio is a Django-based educational platform with Wagtail CMS integration, featuring a dual frontend architecture (React SPA + Django templates), AI-powered programming education, and secure Docker-based code execution.

## Development Commands

### Quick Start (Both Servers)
```bash
# Terminal 1: Django backend (port 8000)
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py runserver

# Terminal 2: React frontend (port 3000/3001)
cd frontend && npm run dev
```

### Backend Commands
```bash
# Database operations
python manage.py makemigrations
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py migrate

# Create test user
python manage.py createsuperuser
# Test credentials: test@pythonlearning.studio / testpass123

# Run tests
python manage.py test apps.learning.tests.test_code_execution  # Specific test
coverage run --source='.' manage.py test && coverage report     # With coverage

# Management commands
python manage.py create_sample_wagtail_content      # Create sample content
python manage.py create_interactive_python_course   # Create interactive course
python manage.py create_step_based_exercise        # Create multi-step exercise
python manage.py rebuild_forum_trackers            # Fix forum statistics
```

### Frontend Commands
```bash
# Modern React (Vite) - PRIMARY
cd frontend
npm install
npm run dev        # Dev server (port 3000/3001)
npm run build      # Production build
npm run lint       # Linting

# Legacy Webpack - SECONDARY
npm install        # From root
npm run build      # Build legacy components
```

### Docker Commands
```bash
docker-compose up                          # Start all services
docker-compose --profile code-execution up # With code execution
docker-compose logs -f code-executor       # View logs
```

## Architecture Overview

### Critical Architecture Decisions

1. **Dual Frontend Architecture**
   - Primary: Modern React SPA (`/frontend`) using Vite, React 18, Tailwind CSS
   - Secondary: Legacy Django templates with embedded React components via Webpack
   - NEW features use React SPA; legacy components only for maintenance

2. **Wagtail Hybrid CMS**
   - Traditional page serving at `/admin`
   - Headless API endpoints at `/api/v1/wagtail/*` for React consumption
   - Two routing patterns: ID-based for Django models, slug-based for Wagtail pages

3. **API Modular Structure** (Refactored 2025-08-10)
   ```
   apps/api/
   ├── viewsets/         # Domain-specific ViewSets
   │   ├── user.py       # User management
   │   ├── learning.py   # Courses, lessons
   │   ├── exercises.py  # Exercise system
   │   └── community.py  # Discussions, groups
   ├── views/            # Function-based views
   │   ├── code_execution.py  # Code execution endpoints
   │   └── wagtail.py         # Wagtail CMS endpoints
   └── services/         # Business logic
       └── code_execution_service.py  # Unified execution with Docker fallback
   ```

4. **Exercise System Architecture**
   - **ExercisePage**: Single exercises with fill-in-blank (`{{BLANK_N}}`) support
   - **StepBasedExercisePage**: Multi-step learning paths with progress tracking
   - **Progressive hints**: Time-based (30s, 90s, 180s, 300s) and attempt-based triggers
   - **Widget system**: CodeMirror 6 with custom `BlankWidget` extending `WidgetType`

5. **Forum Integration** (django-machina)
   - Trust levels (TL0-TL4) with progressive permissions
   - Real-time statistics via `ForumStatisticsService` (no caching for live data)
   - Signal-driven tracker updates on post/topic creation
   - Review queue for moderation with priority scoring
   - **ForumCustomization**: Per-forum icon/color theming (OneToOne with Forum)
   - **PostEditHistory**: Complete edit audit trail with previous content

## API Endpoints

### Authentication
- `POST /api/v1/auth/login/` - JWT token authentication
- `GET /api/v1/auth/user/` - Current user info
- `POST /api/v1/auth/register/` - User registration

### Wagtail Content (Headless CMS)
- `GET /api/v1/wagtail/exercises/` - List exercises with pagination
- `GET /api/v1/wagtail/exercises/{slug}/` - Exercise detail with solutions
- `GET /api/v1/wagtail/step-exercises/{slug}/` - Multi-step exercise detail
- `GET /api/v1/learning/courses/` - Wagtail courses
- `GET /api/v1/blog/` - Blog posts

### Code Execution
- `POST /api/v1/code-execution/` - Execute code in Docker
- `POST /api/v1/exercises/{id}/submit/` - Submit exercise solution
- `GET /api/v1/docker/status/` - Check Docker availability

### Forum (django-machina integration)
- `GET /api/v1/forums/` - List all forums with categories and stats
- `GET /api/v1/forums/{slug}/` - Forum detail with moderators
- `GET /api/v1/forums/{slug}/topics/` - Topics in forum (paginated, filterable)
- `GET /api/v1/forums/{slug}/stats/` - Detailed forum statistics
- `GET /api/v1/topics/{slug}/` - Topic detail with posts
- `POST /api/v1/topics/` - Create new topic (requires authentication)
- `POST /api/v1/posts/` - Create new post (requires authentication)
- `PUT /api/v1/posts/{id}/` - Edit post (creates edit history)
- `GET /api/v1/moderation/queue/` - Review queue (moderators only)
- `POST /api/v1/moderation/queue/{id}/approve/` - Approve pending content
- `POST /api/v1/moderation/queue/{id}/reject/` - Reject pending content
- `GET /api/v1/moderation/statistics/` - Moderation statistics and trends

## Critical Development Patterns

### Exercise Development
```javascript
// Fill-in-blank template format
const template = `# Create a variable
{{BLANK_1}} = {{BLANK_2}}`

// Solutions structure
const solutions = {
  "1": "name",
  "2": "value"
}

// Alternative solutions for flexibility
const alternativeSolutions = {
  "1": ["name", "var", "variable"],
  "2": ["value", "10", "data"]
}
```

### CodeMirror Widget Implementation
```javascript
// Custom widget extends WidgetType
class BlankWidget extends WidgetType {
  toDOM() {
    const input = document.createElement('input')
    // Widget implementation
    return input
  }
  
  ignoreEvent(event) {
    return event.type !== 'mousedown'
  }
}
```

### API Response Patterns
```python
# Consistent error format
return Response({
    'error': 'Error message',
    'details': {...}
}, status=status.HTTP_400_BAD_REQUEST)

# Paginated responses
return Response({
    'results': [...],
    'pagination': {
        'current_page': 1,
        'total_pages': 5,
        'has_next': True
    }
})
```

### Wagtail Page Creation
```python
# Add new Wagtail page type
class NewPageType(Page):
    content_panels = Page.content_panels + [
        FieldPanel('field_name'),
        StreamFieldPanel('content')
    ]
    
    # API serialization
    def get_api_representation(self, request):
        return {
            'id': self.id,
            'title': self.title,
            'content': serialize_streamfield(self.content, request)
        }
```

## Environment Configuration

### Required Environment Variables

#### SECRET_KEY (CRITICAL - REQUIRED)
```bash
# Generate a secure SECRET_KEY first:
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Then add to .env file:
SECRET_KEY=<generated-key-here>
```

**SECURITY REQUIREMENTS:**
- ⚠️ SECRET_KEY is **REQUIRED** - Django will not start without it
- ⚠️ Never use the placeholder `your-super-secret-key-here`
- ⚠️ Never commit SECRET_KEY to version control
- ⚠️ Use different keys for development and production
- ⚠️ Used for: JWT tokens, session cookies, CSRF protection, password resets

#### Other Environment Variables
```bash
# Django Core
DJANGO_SETTINGS_MODULE=learning_community.settings.development
DEBUG=True

# AI Integration
OPENAI_API_KEY=your-api-key  # Optional - graceful fallback if missing

# Database (production only)
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

#### System Dependencies

**libmagic (Required for File Upload Security):**

```bash
# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1 libmagic-dev

# CentOS/RHEL/Fedora
sudo yum install file-devel

# Windows
pip install python-magic-bin

# Verify installation
python3 -c "import magic; print('libmagic installed correctly')"
```

**Why libmagic?**
- Required for CVE-2024-FILE-001 fix (file upload security)
- Detects MIME types from file content (not just extension)
- Prevents extension spoofing attacks
- Graceful degradation if unavailable (reduced security)
- **Strongly recommended for production deployment**

See `DEPENDENCIES.md` for complete installation guide.

## Common Troubleshooting

### Django Settings Issues
```bash
# Always use DJANGO_SETTINGS_MODULE for management commands
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py [command]
```

### Port Conflicts
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
# Vite will auto-use 3001 if 3000 is busy
```

### Forum Statistics Incorrect
```bash
# Rebuild forum trackers
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_forum_trackers
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_topic_trackers
```

### Wagtail Page Tree Issues
```bash
python manage.py fixtree  # Fix page tree structure
```

### Exercise Not Showing
1. Check if published: Exercise must be published in Wagtail admin
2. API URL conflicts: Wagtail exercises use `/api/v1/wagtail/exercises/`
3. Verify slug matches: Use exact slug from Wagtail admin

### File Upload Issues

#### libmagic ImportError
```bash
# Error: "ImportError: failed to find libmagic"
# Solution 1: Install system library
brew install libmagic  # macOS
sudo apt-get install libmagic1  # Ubuntu

# Solution 2: Set library path (macOS)
export DYLD_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_LIBRARY_PATH

# Solution 3: Windows - use bundled version
pip uninstall python-magic
pip install python-magic-bin

# Verify installation
python3 -c "import magic; print('OK')"
```

#### File Upload Validation Errors
```bash
# Check file is valid image
file --mime-type <image-file>
# Should show: image/jpeg, image/png, etc.

# Test with Python
python3 -c "from PIL import Image; img = Image.open('<image-file>'); print(f'{img.format} {img.size}')"

# Check file size
ls -lh <image-file>
# Must be < 5MB for avatars, < 10MB for course images

# Run upload tests
python manage.py test apps.api.tests.test_image_upload_validation -v 2
```

#### Allowed File Formats
- ✅ JPEG (.jpg, .jpeg)
- ✅ PNG (.png)
- ✅ GIF (.gif)
- ✅ WebP (.webp)
- ❌ SVG (.svg) - Removed for XSS prevention
- ❌ All other formats rejected

## Key Implementation Notes

### Adding New Features
1. **Frontend**: Create in `/frontend/src/` using React, Vite, Tailwind
2. **API**: Add ViewSet to `apps/api/viewsets/` or view to `apps/api/views/`
3. **Business Logic**: Extract to `apps/api/services/`
4. **Wagtail Pages**: Define in `apps/blog/models.py`, add API endpoint
5. **Routing**: Update `frontend/src/App.jsx` and `apps/api/urls.py`

### Adding ImageField to Models

When adding ImageField to Django models, ALWAYS use secure upload handlers and validators:

```python
from apps.users.validators import (
    SecureAvatarUpload,  # or appropriate upload handler
    validate_image_file_size,
    validate_mime_type,
    validate_image_content,
    validate_image_dimensions
)

class YourModel(models.Model):
    image = models.ImageField(
        upload_to=SecureAvatarUpload(),  # UUID-based paths
        validators=[
            validate_image_file_size,     # Size limits
            validate_mime_type,            # MIME validation (libmagic)
            validate_image_content,        # Content validation (Pillow)
            validate_image_dimensions,     # Dimension limits
        ],
        blank=True,
        null=True
    )
```

**NEVER:**
- ❌ Use user input in `upload_to` paths
- ❌ Accept user-provided filenames
- ❌ Allow SVG uploads (XSS risk)
- ❌ Skip validation
- ❌ Use extension-only validation

**ALWAYS:**
- ✅ Use UUID-based filenames
- ✅ Validate with python-magic (MIME types)
- ✅ Validate with Pillow (content)
- ✅ Enforce size limits
- ✅ Enforce dimension limits
- ✅ Apply rate limiting to upload endpoints

### Exercise System
- Template syntax: `{{BLANK_N}}` (not `___param___`)
- Solutions: JSON dict mapping blank IDs to answers
- Progressive hints: Array with `triggerTime` and `triggerAttempts`
- Widget validation: Real-time with callback chains

### Forum Development

#### Core Patterns
- Use `ForumStatisticsService` for all stats (not hardcoded values)
- Handle `None` datetime fields in signals
- TL0 users enter review queue automatically
- Tracker updates via signals on post/topic creation

#### Permission Checking with django-machina
```python
from machina.core.loading import get_class
PermissionHandler = get_class('forum_permission.handler', 'PermissionHandler')
perm_handler = PermissionHandler()

# Check forum access
if perm_handler.can_read_forum(forum, user):
    # User can view forum
    pass

# Check moderation permissions
if (perm_handler.can_lock_topics(forum, user) or
    perm_handler.can_delete_topics(forum, user) or
    perm_handler.can_approve_posts(forum, user)):
    # User is moderator for this forum
    pass
```

#### Forum Customization
```python
# Access custom icon/color in serializers
def get_icon(self, obj):
    if hasattr(obj, 'customization'):
        return obj.customization.icon
    return '💬'  # Default emoji

def get_color(self, obj):
    if hasattr(obj, 'customization'):
        return obj.customization.color
    return 'bg-blue-500'  # Default Tailwind class
```

#### Edit History Tracking
```python
from apps.forum_integration.models import PostEditHistory

# Save edit history when updating posts
PostEditHistory.objects.create(
    post=instance,
    edited_by=request.user,
    previous_content=instance.content.raw,
    new_content=validated_data['content'],
    edit_reason=validated_data.get('edit_reason', '')
)

# Retrieve edit history (limited to last 10)
history = PostEditHistory.objects.filter(
    post=obj
).select_related('edited_by').order_by('-edited_at')[:10]
```

#### Trust Level-Based Moderation
```python
# Check if post needs moderation
user = request.user
approved = True

if not user.is_staff and not user.is_superuser:
    if hasattr(user, 'trust_level'):
        # TL0 users need moderation
        if user.trust_level.level == 0:
            approved = False
            # Add to review queue
            from apps.api.services.container import container
            review_service = container.get_review_queue_service()
            review_service.check_new_post(post)
    else:
        # Users without trust level need moderation
        approved = False
```

#### Moderation Statistics
```python
# Get moderation statistics (from ModerationViewSet)
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Avg, Q, F

# Trends (last 7 days)
seven_days_ago = timezone.now() - timedelta(days=7)
trends = ReviewQueue.objects.filter(
    created_at__gte=seven_days_ago
).values('created_at__date').annotate(
    count=Count('id')
).order_by('created_at__date')

# Average response time (approved/rejected items only)
response_time = ReviewQueue.objects.filter(
    status__in=['approved', 'rejected'],
    resolved_at__isnull=False
).annotate(
    response_time=F('resolved_at') - F('created_at')
).aggregate(
    avg_response=Avg('response_time')
)

# Top moderators by action count
top_moderators = ModerationLog.objects.values(
    'moderator__username'
).annotate(
    action_count=Count('id')
).order_by('-action_count')[:5]

# Daily activity breakdown
daily_activity = ReviewQueue.objects.filter(
    created_at__gte=seven_days_ago
).extra(
    select={'day': 'date(created_at)'}
).values('day').annotate(
    pending=Count('id', filter=Q(status='pending')),
    approved=Count('id', filter=Q(status='approved')),
    rejected=Count('id', filter=Q(status='rejected'))
).order_by('day')
```

### Code Execution
- Use `CodeExecutionService` (handles Docker + fallback)
- Docker fails gracefully to basic Python execution
- Resource limits: CPU, memory, time, output size
- Security: Container isolation, no network access

## Testing Strategy

### Backend Testing

#### Run All Tests
```bash
# All tests
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py test

# With coverage
coverage run --source='.' manage.py test && coverage report

# Specific app
python manage.py test apps.learning
python manage.py test apps.forum_integration
python manage.py test apps.api
```

#### Run Specific Tests
```bash
# Single test module
python manage.py test apps.api.tests.test_code_execution
python manage.py test apps.api.tests.test_statistics_service
python manage.py test apps.api.tests.test_review_queue_service
python manage.py test apps.api.tests.test_image_upload_validation

# Single test class
python manage.py test apps.api.tests.test_middleware.MiddlewareTests

# Single test method
python manage.py test apps.api.tests.test_cache_strategies.CacheTests.test_cache_invalidation
```

#### Security Testing
```bash
# All security tests
DJANGO_SETTINGS_MODULE=learning_community.settings.development \
  python manage.py test \
  apps.api.tests.test_xss_protection \
  apps.api.tests.test_csrf_protection \
  apps.api.tests.test_object_permissions \
  apps.api.tests.test_image_upload_validation

# File upload security tests (28 tests)
python manage.py test apps.api.tests.test_image_upload_validation

# Object-level authorization tests (22 tests)
python manage.py test apps.api.tests.test_object_permissions
```

#### Test Files Location
```
apps/
├── api/tests/
│   ├── test_middleware.py
│   ├── test_statistics_service.py
│   ├── test_cache_strategies.py
│   ├── test_review_queue_service.py
│   ├── test_image_upload_validation.py  # File upload security
│   ├── test_object_permissions.py       # IDOR/BOLA prevention
│   ├── test_xss_protection.py          # XSS prevention
│   ├── test_csrf_protection.py         # CSRF protection
│   └── test_commands.py
├── learning/tests.py
├── forum_integration/tests.py
├── blog/tests.py
├── exercises/tests.py
└── users/tests.py
```

### Frontend Testing
```bash
cd frontend && npm test  # When tests are added
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/api/v1/health/

# Authentication
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@pythonlearning.studio","password":"testpass123"}'

# Exercises
curl http://localhost:8000/api/v1/wagtail/exercises/

# Forums
curl http://localhost:8000/api/v1/forums/
```

## Security Implementation Patterns

### Object-Level Authorization (IDOR/BOLA Prevention)
All sensitive API ViewSets implement three-layer defense:

```python
from apps.api.permissions import IsOwnerOrAdmin

class SensitiveResourceViewSet(viewsets.ModelViewSet):
    """ViewSet with object-level authorization."""
    queryset = Model.objects.all()  # For router introspection only
    serializer_class = ModelSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        """Layer 1: Queryset filtering at database level."""
        if self.request.user.is_staff:
            return Model.objects.all()
        return Model.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Layer 3: Ownership forcing prevents hijacking."""
        serializer.save(user=self.request.user)
```

**Security Standards:**
- ✅ Queryset filtering blocks unauthorized access (returns 404)
- ✅ IsOwnerOrAdmin checks multiple ownership patterns (user, author, creator, reviewer)
- ✅ Staff/superuser override for administrative access
- ✅ Ownership forcing prevents mass assignment attacks
- ✅ Test coverage for cross-user access, enumeration, admin override

### XSS Prevention in React
Use centralized sanitization (frontend/src/utils/sanitize.js):

```javascript
import { sanitize } from '@/utils/sanitize';

// Strict mode - no HTML allowed
<div>{sanitize.strict(userInput)}</div>

// Default mode - basic formatting only
<div dangerouslySetInnerHTML={{ __html: sanitize.default(userContent) }} />

// Rich mode - safe HTML subset with link protection
<div dangerouslySetInnerHTML={{ __html: sanitize.rich(blogContent) }} />
```

**Never use raw `dangerouslySetInnerHTML` without sanitization!**

### Authentication & Rate Limiting
All code execution endpoints require authentication and rate limiting:

```python
from apps.api.mixins import RateLimitMixin

class CodeExecutionViewSet(RateLimitMixin, viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]
    rate_limit = '10/minute'  # Configurable per endpoint
```

### File Upload Security (CVE-2024-FILE-001)
All ImageField uploads implement six-layer defense strategy:

```python
from apps.users.validators import (
    SecureAvatarUpload,
    validate_image_file_size,
    validate_image_dimensions,
    validate_image_content,
    validate_mime_type
)

class User(AbstractUser):
    """User model with secure avatar upload."""
    avatar = models.ImageField(
        upload_to=SecureAvatarUpload(),  # Layer 1: UUID-based filenames
        validators=[
            validate_image_file_size,     # Layer 2: Size limits (5MB)
            validate_mime_type,            # Layer 3: MIME validation (python-magic)
            validate_image_content,        # Layer 4: Content validation (Pillow)
            validate_image_dimensions,     # Layer 5: Dimension limits
        ],
        blank=True,
        null=True
    )
```

**Security Features:**
- ✅ UUID-based filenames (no user input in paths)
- ✅ Extension whitelist (JPEG, PNG, GIF, WEBP only)
- ✅ MIME type validation via libmagic (content-based detection)
- ✅ Pillow content validation (prevents polyglot attacks)
- ✅ File size limits (5MB avatars, 10MB course images)
- ✅ Dimension validation (50x50 to 2048x2048 pixels)
- ✅ Rate limiting (10 uploads/minute)
- ❌ SVG support removed (XSS prevention)

**Reusable Validator Pattern (API Serializers):**

```python
from apps.api.validators import ImageUploadValidator

class UserProfileSerializer(serializers.ModelSerializer):
    # Create validator instance
    avatar_validator = ImageUploadValidator(
        max_size_mb=5,
        allow_gif=True,
        field_name='Avatar'
    )

    def validate_avatar(self, value):
        """Validate avatar upload with comprehensive checks."""
        return self.avatar_validator(value)

    class Meta:
        model = User
        fields = ['avatar', ...]
```

**Secure Upload Path Generators:**

```python
from apps.users.validators import (
    SecureAvatarUpload,           # User avatars
    SecureCourseImageUpload,      # Course thumbnails/banners
    SecureIconUpload,             # Programming language icons
    SecureBadgeImageUpload,       # Forum badge images
    SecureAchievementIconUpload   # Achievement icons
)

# Usage in models
class Course(models.Model):
    thumbnail = models.ImageField(
        upload_to=SecureCourseImageUpload('course_thumbnails'),
        validators=[validate_course_image_file_size, ...]
    )
```

**Path Traversal Prevention:**

```python
# NEVER use user input in file paths
# BAD - vulnerable to path traversal
def bad_upload_path(instance, filename):
    return f"uploads/{filename}"  # ❌ filename could be "../../../etc/passwd"

# GOOD - UUID-based paths
def secure_upload_path(instance, filename):
    ext = Path(filename).suffix.lower()
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    ext = ext if ext in ALLOWED_EXTENSIONS else '.jpg'
    return f"avatars/user_{instance.id}/{uuid.uuid4()}{ext}"  # ✅ No user input
```

**Rate Limiting Configuration:**

```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour',
        'file_upload': '10/minute',  # Strict limit for uploads
    }
}

# Apply to ViewSets
from rest_framework.throttling import UserRateThrottle

class FileUploadThrottle(UserRateThrottle):
    scope = 'file_upload'

@action(methods=['POST'], throttle_classes=[FileUploadThrottle])
def upload_avatar(self, request):
    pass
```

**Required System Dependencies:**

File upload security requires **libmagic** for MIME type validation:

```bash
# macOS
brew install libmagic

# Ubuntu/Debian
sudo apt-get install libmagic1 libmagic-dev

# CentOS/RHEL/Fedora
sudo yum install file-devel

# Windows
pip install python-magic-bin

# Verify installation
python3 -c "import magic; print(magic.from_file('/etc/hosts', mime=True))"
```

**Graceful Degradation:**

If libmagic is not installed, validation gracefully degrades:
- ✅ Extension validation still active
- ✅ Content validation (Pillow) still active
- ❌ MIME type validation disabled

**Production deployment strongly recommends libmagic installation for defense-in-depth security.**

**Testing File Uploads:**

```bash
# Run file upload security tests
DJANGO_SETTINGS_MODULE=learning_community.settings.development \
  python manage.py test apps.api.tests.test_image_upload_validation

# Expected: 28 tests, all passing
```

## Recent Updates

### 2025-10-17: File Upload Security (CVE-2024-FILE-001)
1. **Path Traversal Prevention**: UUID-based filenames with zero user input in paths
2. **Six-Layer Defense**: Extension whitelist, MIME validation, content validation, size limits, dimension validation, rate limiting
3. **SVG XSS Prevention**: SVG support removed from all ImageField uploads
4. **ImageUploadValidator**: Reusable validator class for API serializers
5. **libmagic Integration**: Content-based MIME detection (graceful degradation if unavailable)
6. **Race Condition Prevention**: Transaction-based old file cleanup
7. **Security Test Suite**: 28 comprehensive tests covering all attack vectors
8. **Documentation**: Complete file upload security audit, CVE-2024-FILE-001 tracker entry, DEPENDENCIES.md

### 2025-10-17: Critical Security Fixes
1. **IDOR/BOLA Prevention**: Object-level authorization for UserProfile, CourseReview, PeerReview, CodeReview
2. **IsOwnerOrAdmin Permission**: Three-layer defense (queryset filtering, object permissions, ownership forcing)
3. **Security Test Suite**: 22 comprehensive tests covering cross-user access, enumeration, admin override
4. **CVE-2024-IDOR-001**: OWASP API1:2023 vulnerability fixed (PR #17)
5. **Documentation**: Complete CVE tracker, security README, and updated audit reports

### 2025-10-17: Forum Enhancement & TODO Resolution
1. **Forum Customization System**: New `ForumCustomization` model with per-forum icons/colors
2. **Edit History Tracking**: New `PostEditHistory` model for audit trails
3. **Permission Integration**: Complete integration with django-machina's PermissionHandler
4. **Moderation Statistics**: Comprehensive stats (trends, response times, top moderators)
5. **Trust Level Moderation**: TL0 users require approval, TL1+ auto-approved
6. **Avatar System**: Full avatar URL generation in serializers

### 2025-10-16: XSS & Authentication Security
1. **XSS Remediation**: All 23 `dangerouslySetInnerHTML` instances sanitized with DOMPurify
2. **Code Execution Auth**: Authentication required on all code execution endpoints
3. **CSRF Protection**: All 12 @csrf_exempt removed from authenticated endpoints
4. **Template Security**: 2 critical |safe filters fixed in Django templates
5. **Security Test Suite**: 79 tests covering XSS, CSRF, authentication (100% passing)

### 2025-08-11: Exercise & API Systems
1. **Exercise System Complete**: Fill-in-blank and multi-step exercises fully functional
2. **API Refactoring**: Modular structure replacing 3,238-line monolith
3. **Blog/Courses Redesign**: Modern gradient-based design with consistency
4. **StepBasedExercisePage**: New model and React component for multi-step learning
5. **Progressive Hints**: Time and attempt-based hint system implemented