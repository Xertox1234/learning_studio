# CLAUDE.md

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
```bash
# Django
DJANGO_SETTINGS_MODULE=learning_community.settings.development
SECRET_KEY=your-secret-key
DEBUG=True

# AI Integration  
OPENAI_API_KEY=your-api-key  # Optional - graceful fallback if missing

# Database (production only)
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

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

## Key Implementation Notes

### Adding New Features
1. **Frontend**: Create in `/frontend/src/` using React, Vite, Tailwind
2. **API**: Add ViewSet to `apps/api/viewsets/` or view to `apps/api/views/`
3. **Business Logic**: Extract to `apps/api/services/`
4. **Wagtail Pages**: Define in `apps/blog/models.py`, add API endpoint
5. **Routing**: Update `frontend/src/App.jsx` and `apps/api/urls.py`

### Exercise System
- Template syntax: `{{BLANK_N}}` (not `___param___`)
- Solutions: JSON dict mapping blank IDs to answers
- Progressive hints: Array with `triggerTime` and `triggerAttempts`
- Widget validation: Real-time with callback chains

### Forum Development
- Use `ForumStatisticsService` for all stats (not hardcoded values)
- Handle `None` datetime fields in signals
- TL0 users enter review queue automatically
- Tracker updates via signals on post/topic creation

### Code Execution
- Use `CodeExecutionService` (handles Docker + fallback)
- Docker fails gracefully to basic Python execution
- Resource limits: CPU, memory, time, output size
- Security: Container isolation, no network access

## Testing Strategy

```bash
# Run specific app tests
python manage.py test apps.learning
python manage.py test apps.api.tests.test_code_execution

# Frontend testing
cd frontend && npm test  # When tests are added

# Manual testing endpoints
curl http://localhost:8000/api/v1/wagtail/exercises/
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@pythonlearning.studio","password":"testpass123"}'
```

## Recent Updates (2025-08-11)

1. **Exercise System Complete**: Fill-in-blank and multi-step exercises fully functional
2. **API Refactoring**: Modular structure replacing 3,238-line monolith
3. **Blog/Courses Redesign**: Modern gradient-based design with consistency
4. **StepBasedExercisePage**: New model and React component for multi-step learning
5. **Progressive Hints**: Time and attempt-based hint system implemented