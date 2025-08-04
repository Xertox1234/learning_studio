# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python Learning Studio is a comprehensive Django-based educational platform for AI-powered programming education with a **dual frontend architecture**: a modern React SPA and legacy Django templates with embedded React components.

### Core Features
- **Django 5.2.4** with **Wagtail 7.0.1 CMS** for content management
- **Dual Frontend Architecture**: Modern Vite-based React SPA + Legacy Webpack components
- **CodeMirror 6** for advanced code editing with fill-in-the-blank exercises and widget system
- **Docker-based secure code execution** with multi-language support (Python, JS, Java, C++, HTML/CSS)
- **AI integration** via Wagtail AI and OpenAI GPT-4 with progressive hints and floating assistant
- **Complete REST API** with JWT authentication and CORS configuration
- **Advanced forum features** with trust levels, advanced search, and community features
- **Theme system** with dark/light mode support and persistence

## Development Commands

### Backend (Django)
```bash
# Install dependencies
pip install -r requirements.txt

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Run development server (port 8000)
python manage.py runserver

# Run with minimal settings (for development)
python manage.py runserver --settings=learning_community.settings.development_minimal

# Create superuser with demo credentials
python manage.py createsuperuser
# Demo user: test@pythonlearning.studio / testpass123

# Run tests
python manage.py test
python manage.py test apps.learning  # Test specific app
coverage run --source='.' manage.py test && coverage report  # With coverage

# Collect static files
python manage.py collectstatic --noinput
```

### Primary Frontend (Modern React - Vite)
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (port 3000/3001, auto-proxies to Django on 8000)
npm run dev

# Build for production (outputs to /static/react/)
npm run build

# Run linting
npm run lint

# Preview production build
npm run preview
```

### Legacy Frontend (Webpack Components)
```bash
# Install dependencies (from root)
npm install

# Build CodeMirror and React components (outputs to /static/js/dist/)
npm run build

# Watch mode for development
npm run dev
```

### Running Both Servers
```bash
# Terminal 1: Django backend
python manage.py runserver

# Terminal 2: Modern React frontend  
cd frontend && npm run dev

# Access at: http://localhost:3000/ (React) or http://localhost:8000/ (Django)
# Note: If port 3000 is in use, Vite will automatically use 3001
```

### Docker Commands
```bash
# Start all services
docker-compose up

# Start with code execution profile
docker-compose --profile code-execution up

# Build containers
docker-compose build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f
```

### Management Commands

#### Learning Content
```bash
python manage.py create_sample_courses
python manage.py create_structured_content_examples
python manage.py create_fill_blank_example
python manage.py setup_exercise_data
```

#### Forum Features
```bash
python manage.py create_trust_levels
python manage.py calculate_trust_levels
python manage.py trust_level_stats
python manage.py create_default_badges
python manage.py setup_forum_permissions

# Forum maintenance and troubleshooting
# IMPORTANT: Use DJANGO_SETTINGS_MODULE if commands aren't found
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_forum_trackers
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_topic_trackers
python manage.py rebuild_forum_trackers --forum-id 4  # Fix specific forum
python manage.py rebuild_topic_trackers --dry-run     # Preview changes
```

#### Wagtail Content Management
```bash
# Create Wagtail site structure
python manage.py create_wagtail_site

# Generate sample Wagtail content (blog posts, courses, lessons)
python manage.py create_sample_wagtail_content

# Create code playground page with examples
python manage.py create_playground_page

# Wagtail-specific commands
python manage.py update_index          # Update search index
python manage.py fixtree              # Fix page tree structure
python manage.py publish_scheduled    # Publish scheduled pages
```

## Architecture Overview

### Backend Structure
```
apps/
├── api/              # REST API endpoints and authentication
├── blog/             # Blog functionality (Wagtail-based)
├── community/        # Community features and interactions
├── exercises/        # Exercise system (deprecated - use learning app)
├── forum_integration/# Advanced forum features with django-machina
├── frontend/         # Frontend integration app
├── learning/         # Core LMS functionality
└── users/           # User management and profiles
```

### Forum Integration Architecture
The forum system uses **django-machina** as the base forum engine with extensive custom integration:

- **Trust Level System**: Progressive user permissions (TL0-TL4) based on engagement metrics
- **Gamification Service**: Points, badges, and achievements with custom triggers
- **Review Queue System**: Automated moderation with priority scoring based on user trust levels
- **Real-time Features**: WebSocket support for live updates via Django Channels
- **Advanced Search**: Full-text search with filtering across multiple content types
- **Activity Tracking**: Comprehensive user activity monitoring and analytics
- **Signal-Driven Updates**: Django signals automatically update forum/topic trackers on post creation
- **Accurate Statistics Service**: Replaced all hardcoded/mock statistics with `ForumStatisticsService` providing real-time, cached statistics with automatic invalidation
- **Statistics Management**: Advanced forum tracker system with maintenance commands

### Dual Frontend Architecture

#### Primary Frontend (Vite-based React SPA)
```
frontend/                    # Modern React SPA (PRIMARY)
├── src/
│   ├── components/          # Modern React components
│   │   ├── code-editor/     # CodeMirror 6 with widgets (@uiw/react-codemirror)
│   │   │   ├── InteractiveCodeEditor.jsx     # Fill-in-blank exercises
│   │   │   ├── FillInBlankExercise.jsx       # Complete exercise interface
│   │   │   └── ProgressiveHintPanel.jsx      # AI hint system
│   │   ├── common/          # Shared UI components (Tailwind CSS)
│   │   ├── layout/          # Layout and navigation
│   │   └── auth/            # Authentication components
│   ├── contexts/            # React Context (AuthContext, ThemeContext)
│   ├── pages/               # Full page components with routing
│   ├── services/            # API integration layer
│   ├── utils/               # Utility functions and helpers
│   └── App.jsx              # Main router and app setup
├── vite.config.js           # Vite config with Django proxy
└── package.json             # Modern dependencies (React 18, Vite 5, @uiw/react-codemirror, zustand)
```

#### Legacy Frontend (Webpack Components)
```
static/js/                   # Legacy webpack builds (SECONDARY)
├── codemirror6-enhanced.js  # Standalone CodeMirror builds
├── codemirror-themes.js     # Theme switching utilities
├── dist/                    # Webpack output directory
└── [various legacy files]   # Bootstrap-based components
```

### Key Architectural Patterns

1. **Dual Frontend Strategy**: Modern React SPA for new features, legacy components for specific functionality
2. **Hybrid Headless CMS**: Wagtail serves both traditional pages and headless API content for React consumption
3. **Security-First Design**: Docker isolation, resource limits, code validation, JWT authentication
4. **AI Integration**: Wagtail AI backend + custom `LearningContentAI` service with progressive hints
5. **Widget-Based Code Editor**: CodeMirror 6 with custom widgets for fill-in-blank exercises using `{{BLANK_N}}` syntax
6. **Service Layer Pattern**: Business logic encapsulated in `services.py` files across all apps
7. **Context-Driven State**: React Context for auth/theme, Zustand for complex state management
8. **API-First Design**: Complete REST API with comprehensive authentication and CORS support
9. **Signal-Driven Events**: Django signals for forum activity tracking, gamification, and real-time updates
10. **Modular Forum System**: django-machina integration with custom extensions for education-specific features
11. **Wagtail Hybrid CMS**: Traditional Wagtail page serving + headless API endpoints for React consumption
12. **StreamField Integration**: Rich content blocks with API serialization for complex page structures
13. **Live Forum Statistics**: Real-time forum activity data (topics, posts, online users) with selective caching only for static data

## API Structure

Base URL: `/api/v1/`

### Main Endpoints
- `/auth/` - Authentication (login, logout, register)
- `/categories/` - Course categories
- `/courses/` - Course management
- `/lessons/` - Lesson content
- `/exercises/` - Programming exercises
- `/submissions/` - Exercise submissions
- `/code-execution/` - Execute code in Docker
- `/ai-assistance/` - AI-powered help
- `/forums/` - Forum listing and navigation
- `/topics/` - Forum topic CRUD operations
- `/posts/` - Forum post creation and management
- `/dashboard/forum-stats/` - Forum statistics for dashboard

### Wagtail API Endpoints (Hybrid Headless)
- `/blog/` - Blog post listing and detail
- `/blog/categories/` - Blog categories
- `/blog/<slug>/` - Individual blog post
- `/learning/courses/` - Wagtail course pages
- `/learning/courses/<slug>/` - Individual Wagtail course detail
- `/learning/courses/<slug>/lessons/` - Course lessons from Wagtail
- `/wagtail/homepage/` - Homepage content and features
- `/wagtail/playground/` - Code playground configuration and examples

### Authentication
- **JWT tokens** for API authentication (primary for React frontend)
- **Session-based auth** for Django templates/admin interface
- **CORS enabled** for development (localhost:3000/3001 ↔ localhost:8000)
- **Demo credentials**: `test@pythonlearning.studio` / `testpass123`
- **Environment detection**: React frontend auto-detects dev vs prod and routes API calls appropriately

## Code Execution System

### Supported Languages
- Python (3.11)
- JavaScript (Node.js)
- Java
- C++
- HTML/CSS

### Security Features
- Docker container isolation
- Network restrictions
- Resource limits (CPU, memory, time)
- Code pattern validation
- Output size limits

### Docker Configuration
- Custom Docker images for each language
- Volume mounts restricted
- No network access in execution containers
- Automatic cleanup after execution

## Frontend Development

### Modern React Frontend (PRIMARY)

#### CodeMirror 6 Integration
- **React implementation**: `@uiw/react-codemirror` for React-specific integration
- **Fill-in-blank exercises**: `{{BLANK_N}}` syntax replaced with interactive input widgets
- **Widget system**: Custom `BlankWidget` class extending `WidgetType` with `toDOM()` and `ignoreEvent()` methods
- **Template security**: Code template is read-only (`EditorView.editable.of(false)`) while input widgets remain editable
- **Theme integration**: Automatic light/dark mode detection with `useTheme` hook
- **Validation system**: Real-time blank validation with button state management

#### Key Components
- **`InteractiveCodeEditor.jsx`**: Core CodeMirror wrapper with widget decoration system
- **`FillInBlankExercise.jsx`**: Complete exercise interface with validation and AI integration
- **`ProgressiveHintPanel.jsx`**: Time and attempt-based hint system
- **`AIFloatingAssistant.jsx`**: Context-aware AI chatbot with prewritten response buttons
- **`CoursesPage.jsx`**: Comprehensive course listing with search, filtering, and sorting
- **`CourseDetailPage.jsx`**: Full course detail view with lessons, enrollment, and progress tracking  
- **`LessonPage.jsx`**: Individual lesson viewer with content rendering and navigation
- **`WagtailCourseDetailPage.jsx`**: Wagtail course page integration with StreamField content and structured data
- **`WagtailPlaygroundPage.jsx`**: Wagtail-powered code playground with configurable examples and features
- **`BlogIndexPage.jsx`**: Blog listing with category filtering and pagination
- **`BlogPostPage.jsx`**: Individual blog post viewer with rich content blocks
- **`CodeMirrorDemoPage.jsx`**: Development demo page showcasing all CodeMirror components and features

#### State Management
- **AuthContext**: JWT authentication, user management, auto-login detection
- **ThemeContext**: Persistent dark/light mode with system detection
- **Zustand**: Global state for complex cross-component data
- **Local state**: Component-specific UI state and interactions

#### Styling & UI
- **Tailwind CSS**: Utility-first styling with theme-aware classes
- **Responsive design**: Mobile-first approach with breakpoint-specific layouts
- **Theme system**: Consistent dark/light mode across all components
- **Icon library**: Lucide React for consistent iconography

### Legacy Frontend (SUPPLEMENTARY)
- **Bootstrap 5.3**: Traditional component library for legacy templates
- **CodeMirror bundles**: Standalone builds for specific Django template integration
- **Theme switching**: JavaScript-based theme toggle utilities

## Database Models

### Core Models
- **User**: Extended with profile, preferences, achievements
- **Course**: Categories, difficulty levels, AI-enhanced content
- **Lesson**: Sequential content with various types
- **Exercise**: Multiple types with test cases
- **Submission**: Student code submissions with scoring
- **Community**: Forums, discussions, study groups

### Relationships
- Many-to-many: User enrollments, group memberships
- One-to-many: Course lessons, lesson exercises
- Complex: Progress tracking, peer reviews

## Testing

### Backend Testing
```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report

# Test specific components
python manage.py test apps.learning.tests.test_code_execution
```

### Frontend Testing
Frontend tests should be added using Jest and React Testing Library.

## Environment Configuration

### Required Environment Variables
```
# Django
SECRET_KEY=your-secret-key
DEBUG=True  # False in production
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# AI Integration
OPENAI_API_KEY=your-openai-api-key-here

# Redis (for caching)
REDIS_URL=redis://localhost:6379/0

# Email (optional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email
EMAIL_HOST_PASSWORD=your-password
```

## Development Guidelines

### Frontend Development Strategy
- **New features**: Use the modern React frontend (`/frontend/`) with Vite, Tailwind, and React 18
- **Legacy maintenance**: Only modify webpack components when absolutely necessary
- **Authentication**: Always use `useAuth()` hook from `AuthContext` for authentication state
- **API calls**: Use the `utils/api.js` utilities for consistent authentication and error handling
- **Theme support**: Ensure all new components support both light and dark themes using `useTheme()` hook
- **Wagtail integration**: Use slug-based routing for Wagtail content (`/learning/courses/:slug`) vs ID-based for Django models (`/courses/:id`)
- **SEO optimization**: Implement structured data using `utils/schema.js` for course and blog pages
- **CodeMirror components**: Most components are exported from `index.js`, but `CodeEditorErrorBoundary` requires direct import
- **Demo page**: Use `/codemirror-demo` route for testing and development of new CodeMirror features

### Forum Development Patterns
- **Trust Level Integration**: Always check user trust levels before displaying moderation features
- **Signal Safety**: When working with django-machina signals, handle `None` datetime fields in calculations
- **API Consistency**: Use consistent error response format for forum API endpoints
- **Real-time Updates**: Integrate with WebSocket consumers for live forum activity
- **Moderation Queue**: New posts from TL0 users automatically enter review queue
- **Tracker Updates**: Signals automatically call `forum.update_trackers()` and `forum.save()` for new posts/topics
- **Statistics Service**: Use `apps.forum_integration.statistics_service.forum_stats_service` for all forum statistics
- **Live Activity Data**: Topics, posts, and online users are LIVE (no cache) for real-time accuracy
- **Selective Caching**: Only truly static data (total users, latest member) is cached for performance
- **Statistics Maintenance**: Use rebuild commands when forum statistics become inconsistent

### CodeMirror Development Patterns
- **Fill-in-blank syntax**: Always use `{{BLANK_N}}` format (NOT `___param___` or other patterns)
- **Widget implementation**: Extend `WidgetType` with proper `toDOM()` and `ignoreEvent()` methods
- **Template security**: Use `EditorView.editable.of(false)` for read-only templates with editable widgets
- **Theme responsiveness**: Pass theme state to widgets and ensure proper CSS styling
- **Validation**: Implement real-time validation with proper callback chains for button state management
- **Height configuration**: Use appropriate fixed heights for content (e.g., 100px for 2-3 lines, 80px for simple examples)
- **Error boundary imports**: Import `CodeEditorErrorBoundary` directly: `import CodeEditorErrorBoundary from '../components/code-editor/CodeEditorErrorBoundary'`

### API Development
- **Authentication**: JWT tokens for React frontend, session auth for Django templates
- **CORS**: Already configured for development (localhost:3000/3001 ↔ localhost:8000)
- **Error handling**: Use consistent error response format across all endpoints
- **Testing**: Always test API endpoints with both authenticated and unauthenticated requests

### Adding New Exercise Types
1. Define in `apps/learning/models.py` `EXERCISE_TYPE_CHOICES`
2. Create React component in `frontend/src/components/code-editor/`
3. Add API endpoint in `apps/api/views.py` with proper serializer
4. Update frontend routing and navigation
5. Test with both authentication systems

### Creating New Frontend Pages
1. Create component in `frontend/src/pages/`
2. Add route in `frontend/src/App.jsx` with proper protection if needed
3. Create corresponding API service in `frontend/src/services/`
4. Update navigation in `frontend/src/components/layout/`
5. Ensure responsive design and theme support

### Creating New Wagtail Pages
1. Define page model in `apps/blog/models.py` extending `Page`
2. Add content panels, search fields, and parent/child page rules
3. Create template in `templates/blog/` following naming convention
4. Add API endpoint in `apps/api/views.py` for headless consumption
5. Add URL pattern in `apps/api/urls.py`
6. Create corresponding React component if needed
7. Run migrations: `python manage.py makemigrations blog && python manage.py migrate`

## Production Deployment

### Docker Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Run production stack
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### Static Files
```bash
# Build modern React frontend (outputs to /static/react/)
cd frontend && npm run build

# Build legacy webpack components (outputs to /static/js/dist/)
npm run build

# Collect all static files for Django
python manage.py collectstatic --noinput
```

### Security Checklist
- Set `DEBUG=False`
- Configure `ALLOWED_HOSTS`
- Use strong `SECRET_KEY`
- Enable HTTPS
- Configure CORS properly
- Set secure headers

## Troubleshooting

### Common Issues

1. **React frontend connection refused**: 
   - Ensure React dev server is running: `cd frontend && npm run dev`
   - Check if port 3000 is available (Vite will use 3001 if 3000 is occupied)
   - Verify Django backend is running on port 8000

2. **Login fails with "Login Failed"**:
   - Check Django backend is running and accessible
   - Verify CORS settings in `learning_community/settings/development.py`
   - Ensure API base URL detection in `AuthContext.jsx` is working
   - Test backend directly: `curl -X POST http://localhost:8000/api/v1/auth/login/ -H "Content-Type: application/json" -d '{"email":"test@pythonlearning.studio","password":"testpass123"}'`

3. **Forum shows "No posts yet" despite having topics**:
   - Check if topics have posts with `python check_forum_topics.py` (create temporary script)
   - Run `python manage.py rebuild_topic_trackers --forum-id <id>` to fix topic metadata
   - Run `python manage.py rebuild_forum_trackers --forum-id <id>` to update forum statistics
   - Use `--dry-run` flag first to preview changes

4. **Forum topic creation fails with datetime errors**:
   - Check `apps/forum_integration/models.py` ReviewQueue model for `None` datetime fields
   - Ensure `calculate_priority_score()` and `age_in_hours` handle `None` created_at values
   - Fix: Add null checks before datetime arithmetic: `if self.created_at: ...`

5. **CodeMirror theme not changing**: 
   - Ensure `useTheme` hook is properly imported
   - Check theme prop is passed to CodeMirror component with `useMemo` dependency

6. **Fill-in-blank widgets not working**:
   - Use `{{BLANK_N}}` syntax only (not `___param___`)
   - Ensure `BlankWidget` class extends `WidgetType` properly
   - Check `ignoreEvent()` returns `true` for widget events

7. **API authentication errors**: 
   - Verify JWT token in localStorage
   - Check Authorization header format: `Bearer <token>`
   - Use `utils/api.js` utilities for consistent auth handling

8. **Frontend build issues**:
   - For modern React: `cd frontend && npm run build`
   - For legacy webpack: `npm run build` (from root)
   - Clear output directories if builds fail

9. **Forum signals causing errors**:
   - Review signal handlers in `apps/forum_integration/signals.py`
   - Ensure all datetime operations handle potential `None` values
   - Check WebSocket connection issues (Redis required for real-time features)

10. **Course/lesson pages showing "Coming Soon"**:
   - Check if API endpoints exist: `curl http://localhost:8000/api/v1/courses/`
   - Verify routing: Django models use IDs (`/courses/{id}`) while Wagtail uses slugs (`/learning/courses/{slug}`)
   - Ensure both React (port 3000) and Django (port 8000) servers are running
   - Test API directly: `curl http://localhost:8000/api/v1/courses/1/` and `curl http://localhost:8000/api/v1/lessons/1/`

11. **Wagtail pages not loading or 500 errors**:
   - Check StreamField serialization errors in `apps/api/views.py`
   - Verify Wagtail site is created: `python manage.py create_wagtail_site`
   - Check for missing sample content: `python manage.py create_sample_wagtail_content`
   - Review URL routing order in `learning_community/urls.py` - API routes must come before Wagtail catch-all

12. **CodeMirror components not rendering in demo page**:
   - Check import statements - `CodeEditorErrorBoundary` needs direct import
   - Verify component props match expected interface (e.g., `exerciseData` not `exercise`)
   - Ensure proper data structure with `template`, `solutions`, and `alternativeSolutions` fields
   - Use appropriate height values to avoid excessive whitespace

13. **Wagtail playground page not loading**:
   - Ensure CodePlaygroundPage exists: `python manage.py create_playground_page`
   - Check API endpoint accessibility: `curl http://localhost:8000/api/v1/wagtail/playground/`
   - Verify React component can fetch from API (check browser network tab)
   - Ensure page is published in Wagtail admin at `/admin/pages/`

14. **Forum statistics showing false information**:
   - Use `forum_stats_service` for all statistics instead of hardcoded values
   - Run `DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_forum_trackers` to sync database counters
   - Run `DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_topic_trackers` to fix topic post counts
   - Check that cache invalidation signals are working in `apps/forum_integration/cache_signals.py`

### Debug Commands
```bash
# Check Django configuration
python manage.py check

# Show current migrations
python manage.py showmigrations

# Django shell for debugging
python manage.py shell

# Docker container logs
docker-compose logs -f code-executor

# Forum debugging
python manage.py trust_level_stats
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_forum_trackers --dry-run
DJANGO_SETTINGS_MODULE=learning_community.settings.development python manage.py rebuild_topic_trackers --dry-run

# Test forum statistics accuracy
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'learning_community.settings.development')
django.setup()
from apps.forum_integration.statistics_service import forum_stats_service
print('Forum Statistics:', forum_stats_service.get_forum_statistics())
"
```

## Project Status

Python Learning Studio is a **production-ready educational platform** with all core phases complete:

### Completed Features
- ✅ **89 models** created and fully functional across all apps
- ✅ **AI Integration** with Wagtail AI and OpenAI GPT-4 
- ✅ **Docker-based secure code execution** with multi-language support
- ✅ **Complete REST API** with JWT authentication and comprehensive endpoints
- ✅ **Dual frontend architecture** with modern React SPA and legacy components
- ✅ **Advanced forum system** with trust levels, gamification, and real-time features
- ✅ **Live forum statistics** - Real-time forum activity data with no caching for topics, posts, and online users
- ✅ **Theme system** with dark/light mode and persistent user preferences
- ✅ **Community features** including discussions, study groups, and peer learning
- ✅ **Security measures** including container isolation and resource limits
- ✅ **Comprehensive page implementations** - courses listing, course detail, and lesson pages with full functionality
- ✅ **Wagtail-powered pages** - Homepage, blog posts, courses, lessons, and code playground with CMS management

### Technical Architecture
- **Database**: 89 models successfully migrated with complex relationships
- **Frontend**: Dual architecture with Vite-based React SPA + Bootstrap legacy components  
- **Backend**: Django 5.2.4 with Wagtail 7.0.1 CMS and custom service layers
- **Security**: Docker isolation, code validation, JWT authentication, resource limits
- **Performance**: Redis caching, optimized queries, efficient static file handling
- **AI**: Integrated throughout with graceful fallbacks and specialized prompts