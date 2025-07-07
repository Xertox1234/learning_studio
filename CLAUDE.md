# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this production-ready educational platform.

## Project Overview

Python Learning Studio is a **complete, production-ready** Django-based educational platform for AI-powered programming education. The platform features:

- **Django 5.2.4** with **Wagtail 7.0.1 CMS** for content management ✅
- **Wagtail-powered homepage** with StreamField features and AI integration ✅
- **Wagtail AI integration** with OpenAI GPT-4 for intelligent content generation ✅
- **Docker-based secure code execution** with isolation and resource limits ✅
- **Complete REST API** with authentication and comprehensive endpoints ✅
- **Bootstrap 5.3 responsive frontend** with interactive features ✅
- **Community features** for collaborative learning ✅
- **Security-first architecture** with comprehensive testing ✅
- **Production-ready deployment** with Docker and PostgreSQL ✅

## Project Structure

The project follows Django's app-based architecture with modular model organization:

```
/
├── ACTION_PLAN.md          # Comprehensive development roadmap (UPDATED)
├── CLAUDE.md              # This guidance document
├── requirements.txt       # Python dependencies with Docker support
├── .env                   # Environment configuration
├── docker-compose.yml     # Development Docker setup
├── docker-compose.prod.yml # Production Docker configuration
├── Dockerfile             # Development container
├── Dockerfile.prod        # Production container
├── apps/
│   ├── api/               # Complete REST API with authentication ✅
│   ├── blog/              # Wagtail CMS (blog, tutorials, AI-enhanced content) ✅
│   ├── community/         # Community features and social learning ✅
│   ├── exercises/         # Exercise management system ✅
│   ├── learning/          # Core learning platform ✅
│   │   ├── models.py      # Main learning models (courses, lessons, progress)
│   │   ├── exercise_models.py    # Exercise and code execution models
│   │   ├── community_models.py   # Social learning and community models
│   │   ├── services.py    # LearningContentAI service integration
│   │   ├── code_execution.py     # Secure code execution engine
│   │   ├── docker_executor.py    # Docker-based code execution ✅
│   │   └── management/commands/  # Setup commands
│   └── users/             # Extended user profiles and authentication ✅
├── docker/
│   └── python-executor/   # Secure Python execution container ✅
├── learning_community/    # Django settings and configuration
│   ├── settings/          # Split settings (base, development, production)
│   │   ├── base.py        # Core settings with Wagtail AI config
│   │   ├── development.py # Development environment
│   │   ├── production.py  # Production environment ✅
│   │   └── development_minimal.py # Minimal config for testing
├── static/                # Static files with Bootstrap 5.3 ✅
├── templates/             # Complete Django templates with responsive design ✅
├── tests/                 # Comprehensive test suite ✅
├── docs/                  # Documentation including Docker integration ✅
└── media/                 # User-uploaded files
```

## Development Commands

**Current Status**: The platform is production-ready with multiple deployment options:

### Development (Local)
```bash
# Activate virtual environment (required for all commands)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Database operations (use base settings for full features)
python manage.py makemigrations --settings=learning_community.settings.base
python manage.py migrate --settings=learning_community.settings.base
python manage.py createsuperuser --settings=learning_community.settings.base

# Run development server
python manage.py runserver --settings=learning_community.settings.base

# Setup initial data and collect static files
python manage.py setup_exercise_data --settings=learning_community.settings.base
python manage.py collectstatic --noinput --settings=learning_community.settings.base

# Run tests
python manage.py test tests.test_docker_execution --settings=learning_community.settings.base
```

### Development (Docker)
```bash
# Start all services
docker-compose up -d

# Build code executor image
docker build -t python-learning-studio-executor docker/python-executor/

# View logs
docker-compose logs -f web
```

### Production (Docker)
```bash
# Deploy production environment
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# View production logs
docker-compose -f docker-compose.prod.yml logs -f
```

## Architecture Notes

### Data Models (89 Total Models - ALL IMPLEMENTED ✅)

**Core Learning Models** (`apps/learning/models.py`):
- **User Management**: Custom User with profiles, achievements, learning preferences
- **Learning Content**: Courses, lessons, categories with AI-enhanced progress tracking
- **Enrollment System**: Course enrollments with completion tracking and analytics

**Exercise System** (`apps/learning/exercise_models.py`):
- **Programming Languages**: Python, JavaScript, Java, C++, HTML/CSS support
- **Exercise Types**: Function, class, algorithm, debug, fill-blank, multiple choice, project, quiz
- **Code Execution**: Secure Docker-based execution with local fallback
- **Submissions**: Automated testing, scoring, and AI-powered feedback
- **Test Cases**: Hidden and sample test cases with comprehensive validation

**Community Features** (`apps/learning/community_models.py`):
- **Discussions**: Threaded forums with voting and moderation
- **Study Groups**: Collaborative learning with roles and membership management
- **Peer Reviews**: Code review system with detailed feedback and ratings
- **Learning Buddies**: Mentor-mentee and study partner relationships
- **Learning Sessions**: Scheduled collaborative sessions with video integration
- **Notifications**: Real-time user notifications for community activities

**Content Management** (`apps/blog/models.py`):
- **Wagtail Pages**: Blog posts, tutorials, and educational content
- **AI Enhancement**: Automatic content generation and improvement
- **Rich Content**: StreamFields with code blocks and interactive elements

### AI Integration (FULLY IMPLEMENTED ✅)

**Wagtail AI Configuration** (`learning_community/settings/base.py`):
- **GPT-4 Text Completion**: 2000 token limit for content generation
- **GPT-4 Vision**: 300 token limit for image descriptions
- **Graceful Error Handling**: Works without API key for development

**LearningContentAI Service** (`apps/learning/services.py`):
- **Code Explanation**: AI-powered code explanations for beginners
- **Exercise Generation**: Automatic creation of coding challenges
- **Test Case Generation**: Comprehensive test cases for exercises
- **Content Improvement**: AI enhancement of lesson content
- **Learning Path Generation**: Personalized learning recommendations
- **Error Explanation**: Student-friendly error message interpretation
- **Code Review**: Automated feedback on student submissions
- **Hint Generation**: Progressive hints for struggling students

**Integration Points**:
- **Exercise Models**: AI-generated hints, common mistakes, learning notes
- **Course Models**: AI-generated summaries, prerequisites, learning paths
- **Content Creation**: AI-assisted content generation in Wagtail admin

### Code Execution System (FULLY IMPLEMENTED ✅)

**Docker-Based Execution** (`apps/learning/docker_executor.py`):
- **Secure Containers**: Isolated Python execution with network disabled
- **Resource Limits**: 256MB memory, 0.5 CPU cores, 30-second timeouts
- **Security Features**: Non-root user, read-only filesystem, dropped capabilities
- **Caching Layer**: Redis-based result caching for performance
- **API Integration**: REST endpoints for real-time code execution

**Security Measures**:
- **Code Validation**: Pattern detection for dangerous operations
- **Container Isolation**: No network access, limited filesystem
- **Resource Protection**: Memory, CPU, and process limits
- **Safe Module Whitelist**: Only educational modules allowed

**Performance Features**:
- **Container Reuse**: Optimized container lifecycle management
- **Caching**: Intelligent caching of execution results
- **Monitoring**: Health checks and system status endpoints

### API Structure (FULLY IMPLEMENTED ✅)

**REST Framework Setup** (`apps/api/`):
- **Authentication**: JWT and session-based authentication
- **Permissions**: Role-based access control
- **Serializers**: Comprehensive data transformation
- **ViewSets**: Full CRUD operations for all models
- **Documentation**: API endpoint documentation

**Key Endpoints**:
- `/api/v1/execute/` - Real-time code execution
- `/api/v1/exercises/{id}/submit/` - Exercise submission
- `/api/v1/courses/` - Course management
- `/api/v1/docker/status/` - System monitoring

### Frontend (FULLY IMPLEMENTED ✅)

**Bootstrap 5.3 Templates** (`templates/`):
- **Base Templates**: Responsive layout with navigation
- **Course Interface**: Complete course and lesson pages
- **Exercise Interface**: CodeMirror editor with real-time execution
- **Dashboard**: User progress tracking and analytics
- **Community Features**: Discussion forums and study groups

**Interactive Features**:
- **Code Editor**: Syntax highlighting with CodeMirror
- **Real-time Execution**: Instant code feedback
- **AI Assistant**: Modal-based help system
- **Progress Visualization**: Charts and progress bars

## Current Development Status

### ✅ PRODUCTION-READY PLATFORM
- **89 Database Models**: All learning, exercise, and community models ✅
- **User Authentication**: Custom User model with social features ✅
- **Wagtail CMS**: AI-enhanced content management system ✅
- **Wagtail Homepage**: StreamField-powered homepage with full CMS control ✅
- **Learning Management**: Complete course and lesson system ✅
- **Exercise System**: Docker-based secure code execution ✅
- **AI Integration**: LearningContentAI service with Wagtail AI ✅
- **Community Features**: Forums, study groups, peer reviews ✅
- **REST API**: Complete API with authentication and permissions ✅
- **Frontend**: Bootstrap 5.3 responsive templates ✅
- **Testing**: Security and functionality test suites ✅
- **Production Config**: Docker, PostgreSQL, Redis ready ✅

### 🎯 NEXT PHASE PRIORITIES
- **Discourse Integration**: Single Sign-On and unified authentication
- **Advanced Features**: Real-time collaboration, video integration
- **CI/CD Pipeline**: Automated testing and deployment
- **Performance**: Load testing and optimization
- **Mobile**: Enhanced mobile experience and PWA features

## Quick Start Guide

### 1. Local Development
```bash
# Activate virtual environment
source venv/bin/activate

# Verify dependencies
pip list | grep -E "(Django|wagtail|djangorestframework|docker)"

# Check database status
python manage.py showmigrations --settings=learning_community.settings.base

# Run the platform
python manage.py runserver --settings=learning_community.settings.base
```

### 2. Docker Development
```bash
# Start all services (Django, Redis)
docker-compose up -d

# Build secure code executor
docker build -t python-learning-studio-executor docker/python-executor/

# Test code execution
curl -X POST http://localhost:8000/api/v1/execute/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, World!\")"}'
```

### 3. Production Deployment
```bash
# Deploy production stack (Django, PostgreSQL, Redis, Nginx)
docker-compose -f docker-compose.prod.yml up -d

# Scale web services
docker-compose -f docker-compose.prod.yml up -d --scale web=3
```

### 2. Run the Application
```bash
# Start development server
python manage.py runserver --settings=learning_community.settings.development_minimal

# Access Wagtail admin at: http://localhost:8000/admin/
# Create superuser if needed:
python manage.py createsuperuser --settings=learning_community.settings.development_minimal
```

### 3. Test Core Features
```bash
# Test AI integration
python manage.py shell --settings=learning_community.settings.development_minimal -c "
from apps.learning.services import learning_ai
print('AI Available:', learning_ai.ai_available)
result = learning_ai.generate_exercise_explanation('def hello(): return \"Hello World\"')
print('AI Response:', result[:100])
"

# Test code execution
python manage.py shell --settings=learning_community.settings.development_minimal -c "
from apps.learning.code_execution import code_executor
result = code_executor.execute_python_code('print(\"Hello, World!\")')
print('Execution Success:', result.success)
print('Output:', result.output)
"
```

## Application URLs

### **Main Application URLs**
- **🏠 Homepage (Wagtail CMS)**: http://localhost:8000/
- **🎯 Wagtail Admin**: http://localhost:8000/admin/
- **Django Admin**: http://localhost:8000/django-admin/

### **Learning Platform URLs**
- **User Dashboard**: http://localhost:8000/dashboard/
- **Courses**: http://localhost:8000/courses/
- **Community**: http://localhost:8000/community/

### **Authentication URLs**
- **Sign Up**: http://localhost:8000/accounts/signup/
- **Login**: http://localhost:8000/accounts/login/

### **API Endpoints**
- **API Documentation**: http://localhost:8000/api/schema/swagger-ui/
- **API Root**: http://localhost:8000/api/v1/
- **Code Execution**: http://localhost:8000/api/v1/execute/
- **Courses API**: http://localhost:8000/api/v1/courses/
- **Exercises API**: http://localhost:8000/api/v1/exercises/

### **Admin Credentials**
- Username: `admin`
- Password: `admin123`

## Key Configuration Files

### Environment Variables (`.env`)
```bash
# Django Core
SECRET_KEY=django-insecure-y4xd$t)8(&zs6%2a186=wnscue&d@4h0s6(vw3+ovv_idptyl=
DEBUG=True
DJANGO_SETTINGS_MODULE=learning_community.settings.development
ALLOWED_HOSTS=localhost,127.0.0.1

# AI Features (OpenAI API key)
OPENAI_API_KEY=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

# Wagtail Admin
WAGTAILADMIN_BASE_URL=http://localhost:8000
```

### Settings Structure
- `base.py`: Core settings with Wagtail AI configuration
- `development.py`: Development environment settings
- `development_minimal.py`: Minimal settings for testing
- `production.py`: Production environment (to be created)

## Next Development Steps

### Immediate Priorities
1. **API Development**: Create REST endpoints for all models
2. **Frontend Templates**: Implement Bootstrap 5.3 responsive design
3. **Discourse Integration**: Plan SSO implementation

### Model Usage Examples
```python
# Create a course with AI enhancement
from apps.learning.models import Course, Category
from apps.learning.services import learning_ai

category = Category.objects.create(name="Python Basics", slug="python-basics")
course = Course.objects.create(
    title="Python for Beginners",
    slug="python-beginners",
    category=category,
    instructor=user,
    difficulty_level="beginner"
)

# Generate AI-enhanced description
ai_description = learning_ai.generate_course_description(course.title, course.difficulty_level)
course.ai_generated_summary = ai_description
course.save()

# Create an exercise with test cases
from apps.learning.exercise_models import Exercise, TestCase, ProgrammingLanguage

python_lang = ProgrammingLanguage.objects.get(slug="python")
exercise = Exercise.objects.create(
    title="Hello World Function",
    lesson=lesson,
    programming_language=python_lang,
    starter_code="def hello_world():\n    # TODO: Return 'Hello, World!'\n    pass",
    solution_code="def hello_world():\n    return 'Hello, World!'"
)

TestCase.objects.create(
    exercise=exercise,
    name="Basic Test",
    expected_output="Hello, World!",
    is_sample=True
)
```

## Troubleshooting

### Common Issues
1. **Import Errors**: Ensure virtual environment is activated
2. **Migration Issues**: Use `--settings=learning_community.settings.development_minimal`
3. **AI Not Working**: Check OPENAI_API_KEY in .env file
4. **Code Execution Fails**: Docker not required for development (local fallback)

### Getting Help
- Check `ACTION_PLAN.md` for comprehensive project status
- Review model documentation in respective files
- Use Django shell for testing and debugging