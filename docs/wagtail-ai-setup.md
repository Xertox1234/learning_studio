# Wagtail-AI Setup and Configuration Guide

This document outlines the complete setup, configuration, and troubleshooting of Wagtail-AI integration in the Python Learning Studio.

## 📋 Setup Summary

**Status**: ✅ **FULLY OPERATIONAL**  
**Date**: July 5, 2025  
**Wagtail-AI Version**: 2.1.2  
**Django Version**: 4.2.23  
**Wagtail Version**: 7.0.1  

## 🔧 Key Configuration Changes Made

### 1. Django Settings Fixes

#### Base Settings (`learning_community/settings/base.py`)
- ✅ Added `wagtail_ai` to `INSTALLED_APPS`
- ✅ Added `taggit` to resolve Wagtail dependencies
- ✅ Added `allauth.account.middleware.AccountMiddleware` to middleware
- ✅ Configured Wagtail-AI backends for GPT-4 and GPT-4 Vision

#### Development Settings (`learning_community/settings/development.py`)
- ✅ Fixed duplicate `django_extensions` in INSTALLED_APPS
- ✅ Changed session engine to database-based for stability
- ✅ Updated cache configuration to use local memory cache

### 2. Model Fixes

#### User Model References
- ✅ Fixed `apps/learning/models.py` to use `get_user_model()`
- ✅ Fixed `apps/exercises/models.py` to use `get_user_model()`
- ✅ Fixed `apps/api/views.py` import errors for `LearningContentAI`

### 3. URL Configuration

#### Simplified URLs for Development
- ✅ Created `learning_community/urls_simple.py` for stable development
- ✅ Disabled problematic app URLs temporarily during setup
- ✅ Focused on core Wagtail functionality

### 4. Database Setup

#### Migration Management
- ✅ Recreated all migrations from scratch
- ✅ Applied migrations with proper dependency resolution
- ✅ Created superuser account (username: `admin`)

## 🚀 Running the Server

### Development Server Command
```bash
cd /workspaces/Python Learning Studio
export DJANGO_SETTINGS_MODULE=learning_community.settings.development
python manage.py runserver 0.0.0.0:8000
```

### Access Points
- **Wagtail Admin**: <http://localhost:8000/admin/>
- **Django Admin**: <http://localhost:8000/django-admin/>
- **Home Page**: <http://localhost:8000/>

## 🤖 AI Features Verification

### Wagtail-AI Configuration
```python
WAGTAIL_AI = {
    "BACKENDS": {
        "default": {
            "CLASS": "wagtail_ai.ai.openai.OpenAIBackend",
            "CONFIG": {
                "MODEL_ID": "gpt-4",
                "TOKEN_LIMIT": 2000,
            },
        },
        "vision": {
            "CLASS": "wagtail_ai.ai.openai.OpenAIBackend", 
            "CONFIG": {
                "MODEL_ID": "gpt-4-vision-preview",
                "TOKEN_LIMIT": 300,
            },
        },
    },
    "TEXT_COMPLETION_BACKEND": "default",
    "IMAGE_DESCRIPTION_BACKEND": "vision",
}
```

### Custom AI Services
The `LearningContentAI` class provides:
- Exercise explanation generation
- Test case creation
- Learning objective generation
- Code example generation
- Content improvement suggestions

## 🐛 Issues Resolved

### 1. Session Management
**Problem**: `SessionInterrupted` errors during login  
**Solution**: Changed from cache-based to database-based sessions in development

### 2. Django Import Errors
**Problem**: `ModuleNotFoundError: No module named 'django.db.migrations.migration'`  
**Solution**: Complete Django reinstallation and proper environment setup

### 3. Migration Dependencies
**Problem**: Wagtail migration dependency conflicts  
**Solution**: Fresh migration recreation with proper dependency order

### 4. User Model References
**Problem**: `Field defines a relation with the model 'auth.User', which has been swapped out`  
**Solution**: Updated all models to use `get_user_model()`

### 5. Missing Dependencies
**Problem**: Wagtail tags field errors  
**Solution**: Added `taggit` to INSTALLED_APPS

## 📝 Environment Variables Required

```env
# Django Core
SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_SETTINGS_MODULE=learning_community.settings.development

# AI Features
OPENAI_API_KEY=sk-proj-[your-api-key]

# Database (for production)
DB_NAME=learning_community
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

## 🔄 Deployment Checklist

When moving to production:
- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL database
- [ ] Set up Redis for caching and sessions
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Configure static file serving
- [ ] Set up proper logging

## 📊 Current Status

- ✅ Django server running successfully
- ✅ Wagtail admin accessible
- ✅ AI backends configured and operational
- ✅ Custom AI services implemented
- ✅ Session management stable
- ✅ Database migrations applied
- ✅ Superuser account created

## 🔍 Testing AI Features

### In Wagtail Admin
1. Login to <http://localhost:8000/admin/>
2. Create a new page or blog post
3. Use rich text editor with AI buttons
4. Test content generation and improvement features

### Custom AI Services Testing
```python
# In Django shell: python manage.py shell
from apps.learning.services import LearningContentAI

ai = LearningContentAI()
result = ai.generate_exercise_explanation("print('Hello, World!')")
print(result)
```

## 📚 References

- [Wagtail-AI Documentation](https://github.com/wagtail/wagtail-ai)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Django Settings Best Practices](https://docs.djangoproject.com/en/4.2/topics/settings/)
- [Wagtail CMS Documentation](https://wagtail.org/)
