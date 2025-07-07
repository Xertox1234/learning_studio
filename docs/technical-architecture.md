# Technical Architecture & Design Decisions

## WordPress Alternatives Analysis

### Why Not WordPress?
- **Security Concerns**: Frequent security vulnerabilities
- **Performance Issues**: Heavy, plugin-dependent architecture
- **Maintenance Overhead**: Constant updates and plugin management
- **Limited Customization**: Difficult to integrate with modern JavaScript frameworks
- **Developer Experience**: PHP-based, not ideal for modern development workflows

### Modern Blog Solutions (WordPress Alternatives)

#### 1. Next.js + Headless CMS (Recommended)
**Technology Stack:**
- **Frontend**: Next.js 14+ with TypeScript
- **CMS Options**: 
  - **Strapi** (Open source, self-hosted)
  - **Sanity** (Developer-friendly, cloud-based)
  - **Contentful** (Enterprise-grade)
  - **Ghost** (Blog-focused, can be headless)

**Advantages:**
- Lightning-fast static generation
- Excellent SEO with built-in optimization
- Modern developer experience
- Easy content management for non-technical users
- Seamless integration with React components

**Implementation Example:**
```javascript
// pages/blog/[slug].js
export async function getStaticProps({ params }) {
  const post = await getPostBySlug(params.slug);
  return {
    props: { post },
    revalidate: 60 // Regenerate page every minute
  };
}

export async function getStaticPaths() {
  const posts = await getAllPosts();
  return {
    paths: posts.map(post => ({
      params: { slug: post.slug }
    })),
    fallback: 'blocking'
  };
}
```

#### 2. Gatsby + CMS
**Technology Stack:**
- **Frontend**: Gatsby (React-based static site generator)
- **CMS**: Contentful, Strapi, or Forestry
- **Build**: Automatic rebuilds on content changes

**Advantages:**
- Incredible performance with static generation
- Rich plugin ecosystem
- Great for technical content (Markdown support)
- Built-in image optimization

#### 3. Django + Wagtail CMS
**Technology Stack:**
- **Backend**: Django
- **CMS**: Wagtail (Django-based CMS)
- **Frontend**: Django templates or React/Vue.js

**Advantages:**
- Powerful content management interface
- Flexible page structure
- Built-in SEO tools
- Great for complex content types

#### 4. Ghost (Modern Alternative)
**Technology Stack:**
- **Platform**: Ghost (Node.js-based)
- **Usage**: Can be used headless or with built-in themes
- **Content**: Markdown-based writing

**Advantages:**
- Built specifically for blogging
- Excellent writing experience
- Built-in newsletter functionality
- Good SEO out of the box

#### 5. Astro (Modern Static Site Generator)
**Technology Stack:**
- **Framework**: Astro
- **Components**: React, Vue, Svelte (component islands)
- **Content**: Markdown or CMS integration

**Advantages:**
- Minimal JavaScript shipped to browser
- Component island architecture
- Great performance
- Framework agnostic

## Complete Tech Stack Recommendations

### Option 1: Full JavaScript Stack (Recommended)
```yaml
Frontend: Next.js 14+ with TypeScript
Blog: Next.js + Strapi (self-hosted) or Sanity
Learning Platform: Next.js + Custom components
Forum: Discourse (separate service)
Database: PostgreSQL
Authentication: NextAuth.js + Discourse SSO
Code Editor: Monaco Editor (VS Code in browser)
Hosting: Vercel + DigitalOcean
CDN: CloudFlare
Analytics: Plausible or Google Analytics
```

**Monthly Cost Estimate:** $65-$164
- Vercel Pro: $20
- DigitalOcean: $20-40
- Strapi hosting: $0 (self-hosted) or Sanity: $99
- PostgreSQL: $15
- CloudFlare: $20

### Option 2: Django + Wagtail CMS + AI (Updated Recommendation)
**Technology Stack:**
- **Backend**: Django 4.2+
- **CMS**: Wagtail CMS with wagtail-ai addon
- **AI Integration**: wagtail-ai for content generation and assistance
- **Learning Platform**: Django + Custom models
- **Forum**: Discourse (separate service)
- **Database**: PostgreSQL
- **Authentication**: Django-allauth + Discourse SSO

**Wagtail AI Features:**
- **AI-Powered Content Creation**: Built-in AI assistance for writing blog posts
- **Grammar/Spelling Correction**: Automatic content improvement
- **Content Completion**: AI can finish partially written content
- **Image Alt-Text Generation**: Automatic accessibility improvements
- **Custom AI Prompts**: Create custom AI workflows for content
- **Multiple AI Backends**: Support for OpenAI, local models, Claude, Mistral
- **Rich Text Integration**: AI tools directly in the Wagtail editor

**Implementation Example:**
```python
# Django settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'wagtail.core',
    'wagtail.admin',
    'wagtail.documents',
    'wagtail.snippets',
    'wagtail.users',
    'wagtail.images',
    'wagtail.embeds',
    'wagtail.search',
    'wagtail.sites',
    'wagtail.contrib.redirects',
    'wagtail.contrib.forms',
    'wagtail.contrib.sitemaps',
    
    'wagtail_ai',  # AI integration
    
    'learning_platform',  # Your custom learning app
    'community',  # Community features
]

# Wagtail AI Configuration
WAGTAIL_AI = {
    "BACKENDS": {
        "default": {
            "CLASS": "wagtail_ai.ai.openai.OpenAIBackend",
            "CONFIG": {
                "MODEL_ID": "gpt-4",
                "TOKEN_LIMIT": 300,
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
    "IMAGE_DESCRIPTION_PROMPT": "Generate a concise, educational alt-text description for this programming-related image.",
}

# OpenAI API Key (set in environment)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
```

**Content Management Workflow:**
1. **Blog Creation**: Content creators use Wagtail's rich editor
2. **AI Assistance**: Highlight text and click "magic wand" for AI help
3. **Auto-Completion**: AI can finish incomplete blog posts
4. **Grammar Check**: Built-in AI grammar and spelling correction
5. **Image Processing**: Automatic alt-text generation for uploaded images
6. **Custom Prompts**: Create educational content-specific AI prompts

**Advantages for Learning Platform:**
- **Educational Content Focus**: Perfect for creating programming tutorials
- **AI-Enhanced Writing**: Helps content creators write better technical content
- **Accessibility**: Automatic alt-text for images improves accessibility
- **Flexible Content Types**: Support for various content formats
- **SEO Optimization**: Built-in SEO tools
- **Version Control**: Content versioning and workflows
- **Multi-user**: Support for multiple content creators
- **Custom AI Prompts**: Create prompts specific to programming education

**Perfect for Your Use Case Because:**
- **Educational Content**: Wagtail excels at structured educational content
- **AI Integration**: wagtail-ai provides content creation assistance
- **Programming Focus**: Can create custom prompts for code examples, tutorials
- **Multi-Author**: Great for community-driven content creation
- **Rich Media**: Excellent support for images, videos, code blocks
- **Workflow Management**: Editorial workflow for content review

**Monthly Cost Estimate:** $80-$150
- DigitalOcean Droplet: $40-80
- PostgreSQL: $15
- CloudFlare: $20
- OpenAI API Usage: $10-50 (depending on usage)

**Sample AI Prompts for Programming Education:**
```python
# Custom prompts for your learning platform
CUSTOM_PROMPTS = [
    {
        "label": "Explain Code Concept",
        "description": "Break down complex programming concepts",
        "prompt": "Explain this programming concept in simple terms for beginners. Use analogies and examples.",
        "method": "replace"
    },
    {
        "label": "Add Code Examples", 
        "description": "Generate relevant code examples",
        "prompt": "Add practical, well-commented code examples to illustrate this concept.",
        "method": "append"
    },
    {
        "label": "Create Exercise",
        "description": "Generate practice exercises",
        "prompt": "Create a hands-on coding exercise based on this content, including expected output.",
        "method": "append"
    }
]
```

This approach gives you the best of both worlds: a powerful, AI-enhanced CMS for blog content and the flexibility to build custom learning features while maintaining professional content management capabilities.

### Learning Platform Architecture Decision

**Recommendation: Custom Django Apps (Not Wagtail Plugins)**

The learning system should be built as separate Django apps that integrate with Wagtail rather than as Wagtail plugins. Here's the architectural breakdown:

#### Why Custom Django Apps?

1. **Separation of Concerns**: 
   - **Wagtail**: Handles content management (blog, static pages, documentation)
   - **Custom Django Apps**: Handle interactive learning features (courses, exercises, progress tracking)

2. **Complex Data Models**: Learning platforms require sophisticated models that don't fit Wagtail's page-based structure:
   - User progress tracking
   - Interactive code execution
   - Quiz/assessment systems
   - Skill trees and learning paths

3. **API Requirements**: Learning features need REST/GraphQL APIs for:
   - Mobile app integration
   - Interactive JavaScript components
   - Real-time features (code execution, collaborative coding)

4. **Performance**: Custom apps can be optimized for learning-specific operations

#### Recommended Django App Structure

```python
# Project structure
learning_community/
├── settings/
├── urls.py
├── wsgi.py
├── apps/
│   ├── blog/                    # Wagtail CMS for blog content
│   │   ├── models.py           # Wagtail page models
│   │   └── templates/
│   ├── learning/               # Custom Django app for courses
│   │   ├── models.py           # Course, Lesson, Exercise models
│   │   ├── views.py            # Learning views and APIs
│   │   ├── serializers.py      # DRF serializers
│   │   └── templates/
│   ├── exercises/              # Custom Django app for coding exercises
│   │   ├── models.py           # Exercise, Submission models
│   │   ├── code_runner.py      # Code execution engine
│   │   └── validators.py       # Solution validation
│   ├── users/                  # Extended user management
│   │   ├── models.py           # User profiles, progress
│   │   └── views.py            # User dashboards
│   ├── community/              # Community features
│   │   ├── models.py           # Study groups, mentorship
│   │   └── views.py            # Community interactions
│   └── api/                    # Unified API layer
│       ├── urls.py
│       └── views.py
```

#### Integration Strategy

**Content Flow:**
1. **Wagtail CMS**: Blog posts, tutorials, documentation
2. **Custom Apps**: Interactive lessons, exercises, user progress
3. **Shared Components**: User authentication, common templates

**Example Models:**

```python
# apps/learning/models.py
from django.db import models
from django.contrib.auth.models import User
from wagtail.models import Page

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    # Optional: Link to Wagtail page for course overview
    overview_page = models.ForeignKey(
        Page, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Optional Wagtail page for course overview"
    )

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()  # or RichTextField
    order = models.PositiveIntegerField()
    
    # Optional: Link to Wagtail page for lesson content
    content_page = models.ForeignKey(
        Page, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )

class Exercise(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField()
    test_cases = models.JSONField()

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.IntegerField(null=True, blank=True)
```

**Wagtail Integration Example:**

```python
# apps/blog/models.py (Wagtail pages)
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel

class BlogPage(Page):
    body = RichTextField(blank=True)
    
    content_panels = Page.content_panels + [
        FieldPanel('body'),
    ]

class TutorialPage(Page):
    """Tutorial content managed by Wagtail"""
    introduction = RichTextField()
    content = RichTextField()
    
    # Optional: Link to related course
    related_course = models.ForeignKey(
        'learning.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Link to related course in learning platform"
    )
    
    content_panels = Page.content_panels + [
        FieldPanel('introduction'),
        FieldPanel('content'),
        FieldPanel('related_course'),
    ]
```

#### Benefits of This Architecture

1. **Flexibility**: Each system optimized for its purpose
2. **Scalability**: Can scale learning features independently
3. **Maintenance**: Easier to maintain and update
4. **Team Structure**: Different teams can work on different components
5. **Technology Choice**: Can use different tech stacks where appropriate

#### API Integration

```python
# apps/api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.learning.views import CourseViewSet, LessonViewSet
from apps.exercises.views import ExerciseViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'lessons', LessonViewSet)
router.register(r'exercises', ExerciseViewSet)

urlpatterns = [
    path('api/v1/', include(router.urls)),
    path('api/v1/auth/', include('rest_framework.urls')),
]
```

#### Frontend Integration

```javascript
// Frontend can consume both Wagtail pages and custom APIs
// Blog content from Wagtail
const blogPost = await fetch('/api/v2/pages/?type=blog.BlogPage&slug=python-basics');

// Learning content from custom API
const course = await fetch('/api/v1/courses/1/');
const userProgress = await fetch('/api/v1/users/me/progress/');
```

This architecture gives you the best of both worlds: powerful content management through Wagtail for editorial content, and flexible custom Django apps for interactive learning features.

#### Using Wagtail AI in Custom Django Apps

**Yes! You can leverage wagtail-ai features in your custom Django apps.** Here's how to integrate AI capabilities:

##### 1. Direct API Integration

```python
# apps/learning/services.py
from wagtail_ai import ai
from wagtail_ai.models import Prompt
from wagtail_ai.ai.base import BackendFeature

class LearningContentAI:
    """Service class to use Wagtail AI in custom learning apps"""
    
    def generate_exercise_explanation(self, code_snippet):
        """Generate explanation for code exercises"""
        backend = ai.get_backend(BackendFeature.TEXT_COMPLETION)
        
        prompt = "Explain this code in simple terms for beginners learning programming:"
        response = backend.prompt_with_context(
            pre_prompt=prompt,
            context=code_snippet
        )
        return response.text()
    
    def generate_test_cases(self, function_code):
        """Generate test cases for coding exercises"""
        backend = ai.get_backend()
        
        prompt = "Generate comprehensive test cases for this function. Include edge cases:"
        response = backend.prompt_with_context(
            pre_prompt=prompt,
            context=function_code
        )
        return response.text()
    
    def improve_lesson_content(self, lesson_text):
        """Use AI to improve lesson content"""
        backend = ai.get_backend()
        
        prompt = "Improve this programming lesson content for clarity and engagement:"
        response = backend.prompt_with_context(
            pre_prompt=prompt,
            context=lesson_text
        )
        return response.text()
    
    def generate_code_examples(self, concept):
        """Generate code examples for programming concepts"""
        backend = ai.get_backend()
        
        prompt = f"Generate practical, well-commented code examples for this programming concept: {concept}. Include multiple examples with different difficulty levels."
        response = backend.prompt_with_context(
            pre_prompt=prompt,
            context=concept
        )
        return response.text()
```

##### 2. Custom AI Prompts for Learning Platform

```python
# apps/learning/management/commands/setup_ai_prompts.py
from django.core.management.base import BaseCommand
from wagtail_ai.models import Prompt

class Command(BaseCommand):
    help = 'Set up AI prompts for learning platform'
    
    def handle(self, *args, **options):
        # Create custom prompts for learning platform
        prompts = [
            {
                "label": "Generate Code Exercise",
                "description": "Create coding exercises from concepts",
                "prompt": "Create a practical coding exercise for this programming concept. Include: 1) Clear instructions, 2) Starter code template, 3) Expected output, 4) Hints for beginners.",
                "method": "replace"
            },
            {
                "label": "Explain Code Concept",
                "description": "Break down complex programming concepts",
                "prompt": "Explain this programming concept in simple terms suitable for beginners. Use analogies, examples, and step-by-step explanations.",
                "method": "replace"
            },
            {
                "label": "Generate Test Cases",
                "description": "Create comprehensive test cases",
                "prompt": "Generate comprehensive test cases for this code, including edge cases, normal cases, and error conditions. Format as unit tests.",
                "method": "append"
            },
            {
                "label": "Code Review Feedback",
                "description": "Provide constructive code review",
                "prompt": "Review this code and provide constructive feedback focusing on: 1) Code quality, 2) Best practices, 3) Potential improvements, 4) Learning opportunities.",
                "method": "replace"
            },
            {
                "label": "Create Learning Path",
                "description": "Generate structured learning curriculum",
                "prompt": "Create a structured learning path for this programming topic. Include: 1) Prerequisites, 2) Learning objectives, 3) Lesson sequence, 4) Practice exercises.",
                "method": "replace"
            }
        ]
        
        for prompt_data in prompts:
            prompt, created = Prompt.objects.get_or_create(
                label=prompt_data["label"],
                defaults=prompt_data
            )
            if created:
                self.stdout.write(f"Created prompt: {prompt.label}")
```

##### 3. AI-Enhanced Views and Forms

```python
# apps/learning/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .services import LearningContentAI
from .models import Exercise, Lesson
from .forms import ExerciseForm

class AIEnhancedExerciseView:
    """Views with AI integration for exercise management"""
    
    def __init__(self):
        self.ai_service = LearningContentAI()
    
    @csrf_exempt
    def generate_exercise_explanation(self, request):
        """API endpoint to generate exercise explanations"""
        if request.method == 'POST':
            code = request.POST.get('code', '')
            if code:
                explanation = self.ai_service.generate_exercise_explanation(code)
                return JsonResponse({'explanation': explanation})
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    @csrf_exempt
    def generate_test_cases(self, request):
        """API endpoint to generate test cases"""
        if request.method == 'POST':
            function_code = request.POST.get('function_code', '')
            if function_code:
                test_cases = self.ai_service.generate_test_cases(function_code)
                return JsonResponse({'test_cases': test_cases})
        return JsonResponse({'error': 'Invalid request'}, status=400)

# apps/learning/forms.py
from django import forms
from .models import Exercise, Lesson

class AIEnhancedExerciseForm(forms.ModelForm):
    """Form with AI assistance for creating exercises"""
    
    class Meta:
        model = Exercise
        fields = ['title', 'instructions', 'starter_code', 'solution_code']
        widgets = {
            'instructions': forms.Textarea(attrs={
                'class': 'ai-enhanced-textarea',
                'data-ai-prompt': 'Generate Code Exercise'
            }),
            'starter_code': forms.Textarea(attrs={
                'class': 'code-editor',
                'data-ai-help': 'true'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add AI assistance buttons to form
        self.fields['instructions'].help_text = "Use AI assistance to generate exercise instructions"
```

##### 4. Frontend Integration with AI Features

```javascript
// static/js/ai-enhanced-learning.js
class AILearningAssistant {
    constructor() {
        this.setupAIButtons();
    }
    
    setupAIButtons() {
        // Add AI assistance buttons to textareas
        document.querySelectorAll('.ai-enhanced-textarea').forEach(textarea => {
            this.addAIButton(textarea);
        });
    }
    
    addAIButton(textarea) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'ai-assist-btn';
        button.innerHTML = '🪄 AI Assist';
        button.onclick = () => this.generateContent(textarea);
        
        textarea.parentNode.insertBefore(button, textarea.nextSibling);
    }
    
    async generateContent(textarea) {
        const prompt = textarea.dataset.aiPrompt;
        const context = textarea.value;
        
        try {
            const response = await fetch('/learning/ai/generate-content/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    prompt: prompt,
                    context: context
                })
            });
            
            const data = await response.json();
            if (data.content) {
                textarea.value = data.content;
            }
        } catch (error) {
            console.error('AI generation failed:', error);
        }
    }
    
    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new AILearningAssistant();
});
```

##### 5. AI-Enhanced Models

```python
# apps/learning/models.py
from django.db import models
from django.contrib.auth.models import User
from wagtail.models import Page
from .services import LearningContentAI

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty_level = models.CharField(max_length=20)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def generate_ai_description(self):
        """Generate AI-enhanced course description"""
        ai_service = LearningContentAI()
        concept = f"{self.title} - {self.difficulty_level} level course"
        enhanced_description = ai_service.improve_lesson_content(concept)
        return enhanced_description
    
    def generate_learning_objectives(self):
        """Generate AI-powered learning objectives"""
        ai_service = LearningContentAI()
        prompt = f"Generate specific learning objectives for a {self.difficulty_level} level course on {self.title}"
        objectives = ai_service.generate_code_examples(prompt)
        return objectives

class Exercise(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    starter_code = models.TextField(blank=True)
    solution_code = models.TextField()
    test_cases = models.JSONField(default=list)
    
    def generate_ai_test_cases(self):
        """Generate test cases using AI"""
        if self.solution_code:
            ai_service = LearningContentAI()
            test_cases = ai_service.generate_test_cases(self.solution_code)
            return test_cases
        return []
    
    def get_ai_explanation(self):
        """Get AI explanation of the exercise"""
        ai_service = LearningContentAI()
        explanation = ai_service.generate_exercise_explanation(self.solution_code)
        return explanation
```

##### 6. Admin Integration with AI

```python
# apps/learning/admin.py
from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.shortcuts import render
from .models import Course, Lesson, Exercise
from .services import LearningContentAI

@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['title', 'lesson', 'created_at']
    fields = ['lesson', 'title', 'instructions', 'starter_code', 'solution_code']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('ai-generate-test-cases/', self.admin_site.admin_view(self.generate_test_cases_view), name='exercise-ai-test-cases'),
            path('ai-explain-code/', self.admin_site.admin_view(self.explain_code_view), name='exercise-ai-explain'),
        ]
        return custom_urls + urls
    
    def generate_test_cases_view(self, request):
        """Admin view to generate test cases with AI"""
        if request.method == 'POST':
            code = request.POST.get('code', '')
            if code:
                ai_service = LearningContentAI()
                test_cases = ai_service.generate_test_cases(code)
                return JsonResponse({'test_cases': test_cases})
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    def explain_code_view(self, request):
        """Admin view to explain code with AI"""
        if request.method == 'POST':
            code = request.POST.get('code', '')
            if code:
                ai_service = LearningContentAI()
                explanation = ai_service.generate_exercise_explanation(code)
                return JsonResponse({'explanation': explanation})
        return JsonResponse({'error': 'Invalid request'}, status=400)
```

##### Benefits of This Integration:

1. **Reuse AI Infrastructure**: Leverage wagtail-ai's backend configuration and prompts
2. **Consistent AI Experience**: Same AI models across blog and learning platform
3. **Custom Learning Features**: AI-generated exercises, explanations, test cases
4. **Code-Specific Prompts**: Custom prompts tailored for programming education
5. **Admin Integration**: AI assistance in Django admin for content creators
6. **API Endpoints**: RESTful APIs for frontend AI integration

This approach gives you the full power of wagtail-ai's features while maintaining the flexibility of custom Django apps for your learning platform needs.
