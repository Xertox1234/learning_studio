"""
Management command to create initial Wagtail site structure.
Creates HomePage, BlogIndexPage, and sample content.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wagtail.models import Site, Page
from apps.blog.models import HomePage, BlogIndexPage, BlogCategory, BlogPage
from wagtail.blocks import StreamValue
import json
from datetime import date

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates initial Wagtail site structure with HomePage and BlogIndexPage'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Wagtail site structure...')
        
        # Get the root page
        root_page = Page.objects.get(id=1)
        
        # Check if a HomePage already exists
        home_pages = HomePage.objects.all()
        if home_pages.exists():
            self.stdout.write(self.style.WARNING('HomePage already exists. Using existing page.'))
            home_page = home_pages.first()
        else:
            # Create HomePage
            home_page = HomePage(
                title="Python Learning Studio",
                slug="home",
                hero_title="Master Python with AI-Powered Learning",
                hero_subtitle="Join thousands mastering Python through interactive lessons",
                features_title="Why Choose Python Learning Studio?",
            )
            
            # Add features using StreamField
            features_data = [
                {
                    'type': 'feature',
                    'value': {
                        'title': 'AI-Powered Assistance',
                        'description': 'Get instant help with code explanations, error debugging, and personalized hints powered by advanced AI technology.',
                        'icon': 'bi bi-robot'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Real-Time Code Execution',
                        'description': 'Practice coding with instant feedback. Run Python code directly in your browser with our secure, containerized execution environment.',
                        'icon': 'bi bi-terminal'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Interactive Learning',
                        'description': 'Learn by doing with hands-on exercises, fill-in-the-blank challenges, and real-world projects.',
                        'icon': 'bi bi-code-square'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Community Support',
                        'description': 'Join a vibrant community of learners. Ask questions, share knowledge, and grow together.',
                        'icon': 'bi bi-people'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Progress Tracking',
                        'description': 'Track your learning journey with detailed progress reports, achievements, and skill assessments.',
                        'icon': 'bi bi-graph-up'
                    }
                },
                {
                    'type': 'feature',
                    'value': {
                        'title': 'Expert-Crafted Content',
                        'description': 'Learn from carefully designed courses created by experienced Python developers and educators.',
                        'icon': 'bi bi-award'
                    }
                }
            ]
            
            # Convert to StreamValue
            home_page.features = StreamValue(
                stream_block=home_page.features.stream_block,
                stream_data=features_data,
            )
            
            # Add stats
            stats_data = [
                {
                    'type': 'stat',
                    'value': {
                        'number': '10,000+',
                        'label': 'Active Learners',
                        'description': 'Growing community'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '500+',
                        'label': 'Coding Exercises',
                        'description': 'Hands-on practice'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '50+',
                        'label': 'Interactive Courses',
                        'description': 'All skill levels'
                    }
                },
                {
                    'type': 'stat',
                    'value': {
                        'number': '24/7',
                        'label': 'AI Assistance',
                        'description': 'Always available'
                    }
                }
            ]
            
            home_page.stats = StreamValue(
                stream_block=home_page.stats.stream_block,
                stream_data=stats_data,
            )
            
            # Add HomePage as child of root
            root_page.add_child(instance=home_page)
            self.stdout.write(self.style.SUCCESS(f'Created HomePage: {home_page.title}'))
        
        # Update the site to point to our HomePage
        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.root_page = home_page
            site.site_name = "Python Learning Studio"
            site.save()
            self.stdout.write(self.style.SUCCESS('Updated default site root page'))
        else:
            # Create a site if it doesn't exist
            Site.objects.create(
                hostname='localhost',
                port=8000,
                site_name='Python Learning Studio',
                root_page=home_page,
                is_default_site=True
            )
            self.stdout.write(self.style.SUCCESS('Created default site'))
        
        # Check if BlogIndexPage exists
        blog_index_pages = BlogIndexPage.objects.all()
        if blog_index_pages.exists():
            self.stdout.write(self.style.WARNING('BlogIndexPage already exists.'))
            blog_index_page = blog_index_pages.first()
        else:
            # Create BlogIndexPage
            blog_index_page = BlogIndexPage(
                title="Blog",
                slug="blog",
                intro="<p>Explore our latest articles, tutorials, and insights about Python programming, web development, and AI-powered learning.</p>"
            )
            home_page.add_child(instance=blog_index_page)
            self.stdout.write(self.style.SUCCESS(f'Created BlogIndexPage: {blog_index_page.title}'))
        
        # Create blog categories
        categories = [
            {
                'name': 'Python Tutorials',
                'slug': 'python-tutorials',
                'description': 'Step-by-step Python programming tutorials',
                'color': '#3776ab'
            },
            {
                'name': 'AI & Machine Learning',
                'slug': 'ai-ml',
                'description': 'Articles about AI, ML, and their applications',
                'color': '#ff6b6b'
            },
            {
                'name': 'Web Development',
                'slug': 'web-dev',
                'description': 'Web development with Python, Django, and more',
                'color': '#61dafb'
            },
            {
                'name': 'Tips & Tricks',
                'slug': 'tips-tricks',
                'description': 'Quick tips to improve your Python skills',
                'color': '#4ecdc4'
            },
            {
                'name': 'Student Success',
                'slug': 'student-success',
                'description': 'Success stories and learning strategies',
                'color': '#95e1d3'
            }
        ]
        
        for cat_data in categories:
            category, created = BlogCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults={
                    'name': cat_data['name'],
                    'description': cat_data['description'],
                    'color': cat_data['color']
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created category: {category.name}'))
        
        # Create a sample blog post
        if not BlogPage.objects.exists():
            # Get or create a default author
            author = User.objects.filter(is_superuser=True).first()
            if not author:
                author = User.objects.first()
            
            python_category = BlogCategory.objects.get(slug='python-tutorials')
            
            sample_post = BlogPage(
                title="Welcome to Python Learning Studio Blog",
                slug="welcome-python-learning-studio",
                author=author,
                date=date.today(),
                intro="Discover how our AI-powered platform is revolutionizing the way people learn Python programming.",
                reading_time=5,
                ai_generated=False,
                ai_summary="An introduction to Python Learning Studio's blog, featuring insights about AI-powered learning, programming tutorials, and community success stories."
            )
            
            # Add blog content - use proper RichTextBlock format for paragraph values
            body_data = [
                {
                    'type': 'paragraph',
                    'value': 'Welcome to the Python Learning Studio blog! We\'re excited to share our journey of building an AI-powered platform that makes learning Python more accessible, engaging, and effective.'
                },
                {
                    'type': 'heading',
                    'value': 'Why We Built Python Learning Studio'
                },
                {
                    'type': 'paragraph',
                    'value': 'Learning to code can be challenging. Traditional methods often leave students feeling lost, overwhelmed, or unsure of their progress. We built Python Learning Studio to address these challenges by combining:'
                },
                {
                    'type': 'paragraph',
                    'value': '<ul><li><strong>AI-Powered Assistance</strong>: Get help exactly when you need it</li><li><strong>Interactive Exercises</strong>: Learn by doing, not just reading</li><li><strong>Real-Time Feedback</strong>: Know immediately if you\'re on the right track</li><li><strong>Community Support</strong>: Learn alongside others on the same journey</li></ul>'
                },
                {
                    'type': 'callout',
                    'value': {
                        'type': 'info',
                        'title': 'Did You Know?',
                        'text': 'Our AI assistant has helped students debug over 50,000 code snippets and provided personalized learning paths for thousands of learners!'
                    }
                },
                {
                    'type': 'heading',
                    'value': 'What You\'ll Find on This Blog'
                },
                {
                    'type': 'paragraph',
                    'value': 'Our blog will feature a variety of content to support your Python learning journey:'
                },
                {
                    'type': 'paragraph',
                    'value': '<p><strong>Python Tutorials</strong>: From beginner basics to advanced techniques<br><strong>AI & Machine Learning</strong>: Explore the cutting edge of technology<br><strong>Success Stories</strong>: Learn from other students\' experiences<br><strong>Tips & Tricks</strong>: Quick wins to level up your skills<br><strong>Platform Updates</strong>: New features and improvements</p>'
                },
                {
                    'type': 'code',
                    'value': {
                        'language': 'python',
                        'code': '# Your Python journey starts here!\ndef welcome_to_learning():\n    skills = ["problem-solving", "creativity", "logic"]\n    return f"Ready to develop {", ".join(skills)}?"\n\nprint(welcome_to_learning())',
                        'caption': 'Every expert was once a beginner'
                    }
                },
                {
                    'type': 'paragraph',
                    'value': 'Whether you\'re taking your first steps in programming or looking to advance your skills, our blog will be your companion on this exciting journey.'
                },
                {
                    'type': 'callout',
                    'value': {
                        'type': 'tip',
                        'title': 'Get Started Today',
                        'text': 'Ready to begin? Check out our <a href="/courses/">interactive courses</a> or try some <a href="/exercises/">coding exercises</a> to put your skills to the test!'
                    }
                }
            ]
            
            sample_post.body = StreamValue(
                stream_block=sample_post.body.stream_block,
                stream_data=body_data,
            )
            
            blog_index_page.add_child(instance=sample_post)
            
            # Add category after saving
            sample_post.categories.add(python_category)
            
            self.stdout.write(self.style.SUCCESS(f'Created sample blog post: {sample_post.title}'))
        
        self.stdout.write(self.style.SUCCESS('Wagtail site structure created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Homepage URL: http://localhost:8000/'))
        self.stdout.write(self.style.SUCCESS(f'Blog URL: http://localhost:8000/blog/'))
        self.stdout.write(self.style.SUCCESS(f'Admin URL: http://localhost:8000/admin/'))