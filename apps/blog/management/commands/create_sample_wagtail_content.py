"""
Management command to create sample Wagtail content for blog and learning.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from wagtail.models import Page, Site
from apps.blog.models import (
    HomePage, BlogIndexPage, BlogPage, BlogCategory,
    LearningIndexPage, CoursePage, LessonPage, ExercisePage,
    SkillLevel, LearningObjective
)
import datetime
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates sample Wagtail content for blog and learning sections'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample Wagtail content...')
        
        # Get or create superuser
        user = User.objects.filter(is_superuser=True).first()
        if not user:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@pythonlearning.studio',
                password='admin123'
            )
            self.stdout.write(self.style.SUCCESS(f'Created superuser: admin@pythonlearning.studio'))
        
        # Create blog categories
        self.create_blog_categories()
        
        # Create skill levels
        self.create_skill_levels()
        
        # Create learning objectives
        self.create_learning_objectives()
        
        # Get the root page
        root_page = Page.objects.get(id=1)
        
        # Create or get home page
        home_page = HomePage.objects.first()
        if not home_page:
            home_page = self.create_home_page(root_page)
        
        # Create blog structure
        blog_index = self.create_blog_index(home_page)
        self.create_blog_posts(blog_index, user)
        
        # Create learning structure
        learning_index = self.create_learning_index(home_page)
        self.create_courses(learning_index, user)
        
        self.stdout.write(self.style.SUCCESS('Sample Wagtail content created successfully!'))

    def create_blog_categories(self):
        """Create blog categories."""
        categories = [
            {'name': 'Python Basics', 'slug': 'python-basics', 'color': '#3776ab'},
            {'name': 'Web Development', 'slug': 'web-development', 'color': '#61dafb'},
            {'name': 'Data Science', 'slug': 'data-science', 'color': '#ff6b6b'},
            {'name': 'Machine Learning', 'slug': 'machine-learning', 'color': '#4ecdc4'},
            {'name': 'Best Practices', 'slug': 'best-practices', 'color': '#45b7d1'},
        ]
        
        for cat_data in categories:
            BlogCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'color': cat_data['color'],
                    'description': f"Articles about {cat_data['name']}"
                }
            )
        self.stdout.write(self.style.SUCCESS('Created blog categories'))

    def create_skill_levels(self):
        """Create skill levels."""
        levels = [
            {'name': 'Beginner', 'slug': 'beginner', 'order': 1, 'color': '#28a745'},
            {'name': 'Intermediate', 'slug': 'intermediate', 'order': 2, 'color': '#ffc107'},
            {'name': 'Advanced', 'slug': 'advanced', 'order': 3, 'color': '#dc3545'},
        ]
        
        for level_data in levels:
            SkillLevel.objects.get_or_create(
                slug=level_data['slug'],
                defaults={
                    'name': level_data['name'],
                    'order': level_data['order'],
                    'color': level_data['color'],
                    'description': f"{level_data['name']} level content"
                }
            )
        self.stdout.write(self.style.SUCCESS('Created skill levels'))

    def create_learning_objectives(self):
        """Create learning objectives."""
        objectives = [
            {
                'title': 'Master Python Fundamentals',
                'description': 'Learn variables, data types, and control structures',
                'category': 'fundamental'
            },
            {
                'title': 'Build Web Applications',
                'description': 'Create dynamic web apps with Django and Flask',
                'category': 'practical'
            },
            {
                'title': 'Data Analysis with Python',
                'description': 'Use pandas, numpy, and matplotlib for data science',
                'category': 'practical'
            },
            {
                'title': 'Machine Learning Basics',
                'description': 'Understand ML algorithms and implement them in Python',
                'category': 'advanced'
            },
        ]
        
        for obj_data in objectives:
            LearningObjective.objects.get_or_create(
                title=obj_data['title'],
                defaults={
                    'description': obj_data['description'],
                    'category': obj_data['category']
                }
            )
        self.stdout.write(self.style.SUCCESS('Created learning objectives'))

    def create_home_page(self, parent):
        """Create the home page."""
        home_page = HomePage(
            title='Python Learning Studio',
            slug='home',
            hero_title='Master Python Programming',
            hero_subtitle='AI-Powered Learning Platform',
            hero_description='<p>Join thousands mastering Python through interactive lessons, real-time code execution, and AI-powered assistance.</p>',
            features_title='Why Learn With Us?',
            features=json.dumps([
                {
                    'type': 'feature',
                    'value': {
                        'title': 'AI-Powered Assistance',
                        'description': 'Get instant help with code explanations and debugging',
                        'icon': 'bi bi-robot'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Real-Time Code Execution',
                        'description': 'Practice coding with instant feedback in your browser',
                        'icon': 'bi bi-terminal'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Collaborative Learning',
                        'description': 'Join study groups and learn with a supportive community',
                        'icon': 'bi bi-people'
                    }
                }
            ]),
            stats=json.dumps([
                {
                    'type': 'stat',
                    'value': {
                        'number': '10,000+',
                        'label': 'Active Learners',
                        'description': 'Growing community of Python enthusiasts'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '500+',
                        'label': 'Coding Exercises',
                        'description': 'Interactive programming challenges'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '50+',
                        'label': 'Courses',
                        'description': 'Comprehensive learning paths'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '94%',
                        'label': 'Success Rate',
                        'description': 'Student completion percentage'
                    }
                }
            ])
        )
        parent.add_child(instance=home_page)
        
        # Set as the default site homepage
        site = Site.objects.get(is_default_site=True)
        site.root_page = home_page
        site.save()
        
        self.stdout.write(self.style.SUCCESS('Created home page'))
        return home_page

    def create_blog_index(self, parent):
        """Create the blog index page."""
        blog_index = BlogIndexPage.objects.first()
        if not blog_index:
            blog_index = BlogIndexPage(
                title='Blog',
                slug='blog',
                intro='<p>Discover tutorials, insights, and AI-powered learning strategies for Python development.</p>'
            )
            parent.add_child(instance=blog_index)
            self.stdout.write(self.style.SUCCESS('Created blog index page'))
        return blog_index

    def create_blog_posts(self, parent, author):
        """Create sample blog posts."""
        categories = BlogCategory.objects.all()
        
        blog_posts = [
            {
                'title': 'Getting Started with Python: A Beginner\'s Guide',
                'slug': 'getting-started-python-beginners-guide',
                'intro': 'Learn the fundamentals of Python programming with this comprehensive guide for beginners.',
                'categories': ['python-basics'],
                'tags': ['python', 'beginners', 'tutorial'],
                'ai_generated': True,
                'body': [
                    {
                        'type': 'paragraph',
                        'value': '<p>Python is one of the most popular programming languages in the world, known for its simplicity and versatility. Whether you\'re interested in web development, data science, or automation, Python is an excellent choice.</p>'
                    },
                    {
                        'type': 'heading',
                        'value': 'Why Choose Python?'
                    },
                    {
                        'type': 'paragraph',
                        'value': '<p>Python\'s syntax is clean and intuitive, making it perfect for beginners. Its vast ecosystem of libraries and frameworks enables you to build almost anything.</p>'
                    },
                    {
                        'type': 'code',
                        'value': {
                            'language': 'python',
                            'code': '# Your first Python program\nprint("Hello, Python Learning Studio!")\n\n# Variables and data types\nname = "Alice"\nage = 25\nis_student = True\n\nprint(f"{name} is {age} years old")',
                            'caption': 'A simple Python program demonstrating variables'
                        }
                    },
                    {
                        'type': 'callout',
                        'value': {
                            'type': 'tip',
                            'title': 'Pro Tip',
                            'text': '<p>Use meaningful variable names to make your code more readable. Instead of <code>x</code> or <code>y</code>, use descriptive names like <code>user_age</code> or <code>total_price</code>.</p>'
                        }
                    }
                ]
            },
            {
                'title': 'Building Your First Web App with Django',
                'slug': 'building-first-web-app-django',
                'intro': 'Step-by-step guide to creating a web application using Django, Python\'s powerful web framework.',
                'categories': ['web-development'],
                'tags': ['django', 'web', 'framework', 'tutorial'],
                'ai_generated': False,
                'body': [
                    {
                        'type': 'paragraph',
                        'value': '<p>Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design. Let\'s build your first Django application!</p>'
                    },
                    {
                        'type': 'heading',
                        'value': 'Setting Up Django'
                    },
                    {
                        'type': 'code',
                        'value': {
                            'language': 'bash',
                            'code': '# Install Django\npip install django\n\n# Create a new project\ndjango-admin startproject myproject\n\n# Navigate to project directory\ncd myproject\n\n# Run the development server\npython manage.py runserver',
                            'caption': 'Getting started with Django'
                        }
                    },
                    {
                        'type': 'callout',
                        'value': {
                            'type': 'info',
                            'title': 'Django Philosophy',
                            'text': '<p>Django follows the "Don\'t Repeat Yourself" (DRY) principle and includes everything you need to build a web app out of the box.</p>'
                        }
                    }
                ]
            },
            {
                'title': 'Data Science with Python: Pandas Essentials',
                'slug': 'data-science-python-pandas-essentials',
                'intro': 'Master data manipulation and analysis with pandas, the cornerstone of Python data science.',
                'categories': ['data-science'],
                'tags': ['pandas', 'data-science', 'analysis'],
                'ai_generated': True,
                'body': [
                    {
                        'type': 'paragraph',
                        'value': '<p>Pandas is a powerful data manipulation library that makes working with structured data intuitive and efficient. Let\'s explore its core features.</p>'
                    },
                    {
                        'type': 'code',
                        'value': {
                            'language': 'python',
                            'code': 'import pandas as pd\nimport numpy as np\n\n# Create a DataFrame\ndata = {\n    \'Name\': [\'Alice\', \'Bob\', \'Charlie\', \'Diana\'],\n    \'Age\': [25, 30, 35, 28],\n    \'City\': [\'NYC\', \'LA\', \'Chicago\', \'Boston\'],\n    \'Salary\': [70000, 85000, 95000, 80000]\n}\n\ndf = pd.DataFrame(data)\n\n# Basic operations\nprint(df.head())\nprint(f"Average salary: ${df[\'Salary\'].mean():,.2f}")\nprint(f"Oldest person: {df.loc[df[\'Age\'].idxmax(), \'Name\']}")',
                            'caption': 'Working with pandas DataFrames'
                        }
                    },
                    {
                        'type': 'callout',
                        'value': {
                            'type': 'warning',
                            'title': 'Memory Usage',
                            'text': '<p>When working with large datasets, be mindful of memory usage. Use <code>dtype</code> parameter to optimize memory consumption.</p>'
                        }
                    }
                ]
            },
            {
                'title': 'Introduction to Machine Learning with Scikit-learn',
                'slug': 'introduction-machine-learning-scikit-learn',
                'intro': 'Get started with machine learning in Python using scikit-learn, the go-to library for ML practitioners.',
                'categories': ['machine-learning'],
                'tags': ['machine-learning', 'scikit-learn', 'AI'],
                'ai_generated': False,
                'body': [
                    {
                        'type': 'paragraph',
                        'value': '<p>Machine learning is transforming how we solve problems. Scikit-learn makes it accessible to everyone with its simple and consistent API.</p>'
                    },
                    {
                        'type': 'heading',
                        'value': 'Your First ML Model'
                    },
                    {
                        'type': 'code',
                        'value': {
                            'language': 'python',
                            'code': 'from sklearn.datasets import load_iris\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.tree import DecisionTreeClassifier\nfrom sklearn.metrics import accuracy_score\n\n# Load dataset\niris = load_iris()\nX, y = iris.data, iris.target\n\n# Split data\nX_train, X_test, y_train, y_test = train_test_split(\n    X, y, test_size=0.2, random_state=42\n)\n\n# Train model\nclf = DecisionTreeClassifier(random_state=42)\nclf.fit(X_train, y_train)\n\n# Make predictions\ny_pred = clf.predict(X_test)\naccuracy = accuracy_score(y_test, y_pred)\n\nprint(f"Model accuracy: {accuracy:.2%}")',
                            'caption': 'Training a simple classification model'
                        }
                    }
                ]
            },
            {
                'title': 'Python Best Practices: Writing Clean Code',
                'slug': 'python-best-practices-clean-code',
                'intro': 'Learn how to write Python code that is readable, maintainable, and follows community standards.',
                'categories': ['best-practices'],
                'tags': ['clean-code', 'best-practices', 'PEP8'],
                'ai_generated': True,
                'body': [
                    {
                        'type': 'paragraph',
                        'value': '<p>Writing clean code is essential for long-term project success. Let\'s explore Python best practices that will make your code a joy to work with.</p>'
                    },
                    {
                        'type': 'heading',
                        'value': 'The Zen of Python'
                    },
                    {
                        'type': 'code',
                        'value': {
                            'language': 'python',
                            'code': '# Good: Clear and explicit\ndef calculate_total_price(price, tax_rate):\n    """Calculate total price including tax."""\n    tax_amount = price * tax_rate\n    total = price + tax_amount\n    return total\n\n# Bad: Unclear and implicit\ndef calc(p, t):\n    return p + p * t\n\n# Good: Using type hints\nfrom typing import List, Dict\n\ndef process_users(users: List[Dict[str, str]]) -> List[str]:\n    """Extract and return user names from user data."""\n    return [user["name"] for user in users if "name" in user]',
                            'caption': 'Examples of clean vs unclear code'
                        }
                    },
                    {
                        'type': 'quote',
                        'value': {
                            'text': 'Beautiful is better than ugly. Explicit is better than implicit. Simple is better than complex.',
                            'attribution': 'The Zen of Python'
                        }
                    }
                ]
            }
        ]
        
        for i, post_data in enumerate(blog_posts):
            # Skip if already exists
            if BlogPage.objects.filter(slug=post_data['slug']).exists():
                continue
                
            post = BlogPage(
                title=post_data['title'],
                slug=post_data['slug'],
                intro=post_data['intro'],
                author=author,
                date=datetime.date.today() - datetime.timedelta(days=i * 7),
                body=json.dumps(post_data['body']),
                ai_generated=post_data['ai_generated'],
                ai_summary=f"This article covers {post_data['title'].lower()} with practical examples and best practices.",
                reading_time=5 + i
            )
            parent.add_child(instance=post)
            
            # Add categories
            for cat_slug in post_data['categories']:
                category = BlogCategory.objects.get(slug=cat_slug)
                post.categories.add(category)
            
            # Add tags
            for tag in post_data['tags']:
                post.tags.add(tag)
            
            post.save()
            
        self.stdout.write(self.style.SUCCESS(f'Created {len(blog_posts)} blog posts'))

    def create_learning_index(self, parent):
        """Create the learning index page."""
        learning_index = LearningIndexPage.objects.first()
        if not learning_index:
            learning_index = LearningIndexPage(
                title='Learning Hub',
                slug='learning',
                intro='<p>Explore our comprehensive Python courses designed to take you from beginner to expert.</p>',
                featured_courses_title='Featured Courses'
            )
            parent.add_child(instance=learning_index)
            self.stdout.write(self.style.SUCCESS('Created learning index page'))
        return learning_index

    def create_courses(self, parent, instructor):
        """Create sample courses with lessons and exercises."""
        skill_levels = SkillLevel.objects.all()
        objectives = LearningObjective.objects.all()
        categories = BlogCategory.objects.all()
        
        courses = [
            {
                'title': 'Python Fundamentals',
                'slug': 'python-fundamentals',
                'course_code': 'PY101',
                'short_description': 'Master the basics of Python programming from variables to functions.',
                'detailed_description': '<p>This comprehensive course covers all the fundamental concepts you need to start programming in Python. Perfect for absolute beginners!</p>',
                'skill_level': 'beginner',
                'difficulty_level': 'beginner',
                'estimated_duration': '4 weeks',
                'is_free': True,
                'featured': True,
                'lessons': [
                    {
                        'title': 'Introduction to Python',
                        'slug': 'introduction-to-python',
                        'lesson_number': 1,
                        'intro': 'Get started with Python by learning about its history, philosophy, and setting up your development environment.',
                        'content': [
                            {
                                'type': 'text',
                                'value': '<p>Welcome to Python! In this lesson, we\'ll explore what makes Python special and set up everything you need to start coding.</p>'
                            },
                            {
                                'type': 'code_example',
                                'value': {
                                    'title': 'Your First Python Program',
                                    'language': 'python',
                                    'code': 'print("Welcome to Python Learning Studio!")\nprint("Let\'s start learning Python together!")',
                                    'explanation': '<p>The <code>print()</code> function displays text on the screen. It\'s often the first thing you learn in any programming language!</p>'
                                }
                            }
                        ]
                    },
                    {
                        'title': 'Variables and Data Types',
                        'slug': 'variables-and-data-types',
                        'lesson_number': 2,
                        'intro': 'Learn how to store and manipulate data using variables and understand Python\'s built-in data types.',
                        'content': [
                            {
                                'type': 'text',
                                'value': '<p>Variables are containers for storing data values. Python has several built-in data types.</p>'
                            },
                            {
                                'type': 'interactive_exercise',
                                'value': {
                                    'title': 'Create Your First Variables',
                                    'instructions': '<p>Create variables for your name, age, and whether you\'re a student.</p>',
                                    'starter_code': '# Create your variables here\nname = {{BLANK_1}}\nage = {{BLANK_2}}\nis_student = {{BLANK_3}}\n\n# Print them out\nprint(f"Name: {name}")\nprint(f"Age: {age}")\nprint(f"Student: {is_student}")',
                                    'solution': 'name = "Alice"\nage = 25\nis_student = True',
                                    'hints': ['Names should be in quotes', 'Age is a number', 'is_student should be True or False']
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'title': 'Web Development with Django',
                'slug': 'web-development-django',
                'course_code': 'WEB201',
                'short_description': 'Build dynamic web applications using Django, Python\'s premier web framework.',
                'detailed_description': '<p>Learn to build professional web applications with Django. From models to views to templates, master the MTV architecture!</p>',
                'skill_level': 'intermediate',
                'difficulty_level': 'intermediate',
                'estimated_duration': '6 weeks',
                'is_free': False,
                'price': '49.99',
                'featured': True,
                'lessons': [
                    {
                        'title': 'Django Project Setup',
                        'slug': 'django-project-setup',
                        'lesson_number': 1,
                        'intro': 'Set up your first Django project and understand the project structure.',
                        'content': [
                            {
                                'type': 'text',
                                'value': '<p>Django projects have a specific structure that helps organize your code effectively.</p>'
                            },
                            {
                                'type': 'code_example',
                                'value': {
                                    'title': 'Creating a Django Project',
                                    'language': 'bash',
                                    'code': 'django-admin startproject mysite\ncd mysite\npython manage.py runserver',
                                    'explanation': '<p>These commands create a new Django project and start the development server.</p>'
                                }
                            }
                        ]
                    }
                ]
            },
            {
                'title': 'Data Science Masterclass',
                'slug': 'data-science-masterclass',
                'course_code': 'DS301',
                'short_description': 'Comprehensive data science course covering pandas, numpy, matplotlib, and machine learning.',
                'detailed_description': '<p>Dive deep into data science with Python. Learn to analyze, visualize, and extract insights from data using industry-standard tools.</p>',
                'skill_level': 'advanced',
                'difficulty_level': 'advanced',
                'estimated_duration': '8 weeks',
                'is_free': False,
                'price': '99.99',
                'featured': False,
                'lessons': []
            }
        ]
        
        for course_data in courses:
            # Skip if already exists
            if CoursePage.objects.filter(slug=course_data['slug']).exists():
                continue
                
            # Get skill level
            skill_level = skill_levels.filter(slug=course_data['skill_level']).first()
            
            # Create course
            course = CoursePage(
                title=course_data['title'],
                slug=course_data['slug'],
                course_code=course_data['course_code'],
                short_description=course_data['short_description'],
                detailed_description=course_data['detailed_description'],
                instructor=instructor,
                skill_level=skill_level,
                difficulty_level=course_data['difficulty_level'],
                estimated_duration=course_data['estimated_duration'],
                is_free=course_data['is_free'],
                price=course_data.get('price'),
                featured=course_data['featured'],
                prerequisites='<p>Basic computer skills and enthusiasm to learn!</p>',
                syllabus=json.dumps([
                    {
                        'type': 'module',
                        'value': {
                            'title': 'Module 1: Getting Started',
                            'description': '<p>Foundation concepts and environment setup</p>',
                            'lessons': [
                                {
                                    'lesson_title': 'Course Introduction',
                                    'lesson_description': 'Overview of what you\'ll learn',
                                    'estimated_time': '30 minutes'
                                }
                            ]
                        }
                    }
                ]),
                features=json.dumps([
                    {
                        'type': 'feature',
                        'value': {
                            'icon': '🎯',
                            'title': 'Hands-on Projects',
                            'description': 'Build real-world applications'
                        }
                    },
                    {
                        'type': 'feature',
                        'value': {
                            'icon': '🤖',
                            'title': 'AI Assistance',
                            'description': 'Get help when you\'re stuck'
                        }
                    },
                    {
                        'type': 'feature',
                        'value': {
                            'icon': '📱',
                            'title': 'Mobile Friendly',
                            'description': 'Learn on any device'
                        }
                    }
                ])
            )
            parent.add_child(instance=course)
            
            # Add categories and objectives
            course.categories.add(categories.first())
            course.learning_objectives.add(objectives.first())
            course.save()
            
            # Create lessons for this course
            for lesson_data in course_data['lessons']:
                lesson = LessonPage(
                    title=lesson_data['title'],
                    slug=lesson_data['slug'],
                    lesson_number=lesson_data['lesson_number'],
                    estimated_duration='30 minutes',
                    intro=lesson_data['intro'],
                    content=json.dumps(lesson_data['content']),
                    lesson_objectives=json.dumps([
                        {'type': 'objective', 'value': 'Understand the basics'},
                        {'type': 'objective', 'value': 'Write your first code'},
                    ]),
                    resources=json.dumps([
                        {
                            'type': 'resource',
                            'value': {
                                'title': 'Python Official Documentation',
                                'url': 'https://docs.python.org',
                                'description': 'The official Python documentation',
                                'type': 'documentation'
                            }
                        }
                    ])
                )
                course.add_child(instance=lesson)
                
                # Create an exercise for the lesson
                if lesson_data['lesson_number'] == 2:  # Add exercise to second lesson
                    exercise = ExercisePage(
                        title='Practice Variables',
                        slug='practice-variables',
                        exercise_type='fill_blank',
                        difficulty='easy',
                        points=10,
                        description='<p>Practice creating and using variables in Python.</p>',
                        starter_code='# Create a variable called message\nmessage = {{BLANK_1}}\n\n# Create a variable called count\ncount = {{BLANK_2}}\n\n# Print both variables\nprint(f"Message: {message}")\nprint(f"Count: {count}")',
                        solution_code='message = "Hello Python"\ncount = 42',
                        programming_language='python',
                        test_cases=json.dumps([
                            {
                                'type': 'test_case',
                                'value': {
                                    'input': '',
                                    'expected_output': 'Message: Hello Python\nCount: 42',
                                    'description': 'Check variable creation',
                                    'is_hidden': False
                                }
                            }
                        ]),
                        hints=json.dumps([
                            {
                                'type': 'hint',
                                'value': {
                                    'hint_text': '<p>Remember: strings need quotes around them!</p>',
                                    'reveal_after_attempts': 2
                                }
                            },
                            {
                                'type': 'hint',
                                'value': {
                                    'hint_text': '<p>The count should be a number (integer).</p>',
                                    'reveal_after_attempts': 3
                                }
                            }
                        ])
                    )
                    lesson.add_child(instance=exercise)
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(courses)} courses with lessons'))