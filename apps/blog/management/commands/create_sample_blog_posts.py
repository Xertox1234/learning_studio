from django.core.management.base import BaseCommand
from wagtail.models import Page, Site
from apps.blog.models import BlogPage, BlogIndexPage
from wagtail.rich_text import RichText


class Command(BaseCommand):
    help = 'Creates 3 sample blog posts for demonstration'

    def handle(self, *args, **options):
        # Get or create BlogIndexPage
        try:
            blog_index = BlogIndexPage.objects.first()
            if not blog_index:
                # Get root page
                root_page = Page.objects.get(depth=1).specific
                blog_index = BlogIndexPage(
                    title='Blog',
                    slug='blog',
                    show_in_menus=True
                )
                root_page.add_child(instance=blog_index)
                blog_index.save_revision().publish()
                self.stdout.write(self.style.SUCCESS('Created BlogIndexPage'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating BlogIndexPage: {e}'))
            return

        # Sample blog posts
        posts = [
            {
                'title': 'Getting Started with Python: Your First Steps',
                'slug': 'getting-started-with-python',
                'intro': 'Learn the fundamentals of Python programming and start your coding journey today.',
                'body_blocks': [
                    ('heading', 'Welcome to Python Programming!'),
                    ('paragraph', '<p>Python is one of the most popular and versatile programming languages in the world. Whether you\'re interested in web development, data science, automation, or artificial intelligence, Python is an excellent choice.</p>'),
                    ('heading', 'Why Choose Python?'),
                    ('paragraph', '<ul><li><strong>Easy to Learn:</strong> Python\'s syntax is clear and readable, making it perfect for beginners</li><li><strong>Powerful Libraries:</strong> Access thousands of libraries for any task imaginable</li><li><strong>Great Community:</strong> Millions of developers ready to help and share knowledge</li><li><strong>Career Opportunities:</strong> High demand in tech, finance, research, and more</li></ul>'),
                    ('heading', 'Your First Python Program'),
                    ('paragraph', '<p>Let\'s start with the traditional "Hello, World!" program:</p>'),
                    ('code', {
                        'language': 'python',
                        'code': 'print("Hello, World!")',
                        'caption': 'Your first Python program'
                    }),
                    ('paragraph', '<p>That\'s it! Just one line of code. Python makes programming accessible and fun.</p>'),
                    ('heading', 'What\'s Next?'),
                    ('paragraph', '<p>After mastering the basics, you can explore:</p><ul><li>Variables and data types</li><li>Control flow (if statements, loops)</li><li>Functions and modules</li><li>Object-oriented programming</li></ul>'),
                    ('callout', {
                        'type': 'tip',
                        'title': 'Start Practicing',
                        'text': '<p>Check out our interactive exercises to practice what you\'ve learned!</p>'
                    }),
                ],
                'tags': ['beginner', 'python-basics', 'tutorial']
            },
            {
                'title': 'Mastering Python Lists: Tips and Tricks',
                'slug': 'mastering-python-lists',
                'intro': 'Dive deep into Python lists with practical examples and advanced techniques.',
                'body_blocks': [
                    ('heading', 'Python Lists: More Than Just Arrays'),
                    ('paragraph', '<p>Lists are one of Python\'s most fundamental and versatile data structures. They\'re like Swiss Army knives for storing and manipulating collections of data.</p>'),
                    ('heading', 'Basic List Operations'),
                    ('paragraph', '<p>Creating and accessing lists is straightforward:</p>'),
                    ('code', {
                        'language': 'python',
                        'code': '''fruits = ['apple', 'banana', 'cherry']
print(fruits[0])  # Output: apple
fruits.append('orange')
print(len(fruits))  # Output: 4''',
                        'caption': 'Basic list operations'
                    }),
                    ('heading', 'List Comprehensions: Python\'s Secret Weapon'),
                    ('paragraph', '<p>List comprehensions let you create lists in a single, elegant line:</p>'),
                    ('code', {
                        'language': 'python',
                        'code': '''# Traditional way
squares = []
for x in range(10):
    squares.append(x**2)

# List comprehension way
squares = [x**2 for x in range(10)]''',
                        'caption': 'List comprehensions vs traditional loops'
                    }),
                    ('heading', 'Advanced Techniques'),
                    ('paragraph', '<ul><li><strong>Slicing:</strong> Extract portions of lists with ease</li><li><strong>Unpacking:</strong> Assign multiple variables at once</li><li><strong>Zip:</strong> Combine multiple lists together</li><li><strong>Filter:</strong> Select items that meet conditions</li></ul>'),
                    ('callout', {
                        'type': 'info',
                        'title': 'Performance Tips',
                        'text': '<p>Lists are great, but remember:</p><ul><li>Use tuples for immutable data</li><li>Consider sets for unique items</li><li>Try deques for queue operations</li></ul>'
                    }),
                    ('paragraph', '<p>Ready to practice? Try our list manipulation exercises!</p>'),
                ],
                'tags': ['intermediate', 'data-structures', 'lists']
            },
            {
                'title': 'Building Web APIs with Django REST Framework',
                'slug': 'building-web-apis-django-rest',
                'intro': 'Learn how to create powerful RESTful APIs using Django REST Framework.',
                'body_blocks': [
                    ('heading', 'Django REST Framework: APIs Made Easy'),
                    ('paragraph', '<p>Django REST Framework (DRF) is the go-to solution for building Web APIs in Python. It provides a powerful and flexible toolkit that makes API development a breeze.</p>'),
                    ('heading', 'Why Django REST Framework?'),
                    ('paragraph', '<ul><li><strong>Built on Django:</strong> Leverage Django\'s ORM, authentication, and ecosystem</li><li><strong>Serialization:</strong> Convert complex data types to JSON effortlessly</li><li><strong>ViewSets:</strong> Write less code with powerful class-based views</li><li><strong>Authentication:</strong> Multiple auth options out of the box</li></ul>'),
                    ('heading', 'Quick Example: A Simple API'),
                    ('code', {
                        'language': 'python',
                        'code': '''# models.py
class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=100)
    published_date = models.DateField()

# serializers.py
class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'published_date']

# views.py
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer''',
                        'caption': 'A complete DRF API in just a few lines'
                    }),
                    ('heading', 'Key Concepts to Master'),
                    ('paragraph', '<ol><li><strong>Serializers:</strong> Transform data between Python and JSON</li><li><strong>ViewSets:</strong> Handle CRUD operations automatically</li><li><strong>Routers:</strong> Generate URL patterns automatically</li><li><strong>Permissions:</strong> Control who can access what</li></ol>'),
                    ('callout', {
                        'type': 'tip',
                        'title': 'Best Practices',
                        'text': '<ul><li>Use pagination for large datasets</li><li>Implement proper error handling</li><li>Version your API endpoints</li><li>Write comprehensive tests</li><li>Document with Swagger/OpenAPI</li></ul>'
                    }),
                    ('paragraph', '<p>This platform itself is built with Django REST Framework! Explore our API endpoints to see these concepts in action.</p>'),
                ],
                'tags': ['advanced', 'django', 'web-development', 'api']
            }
        ]

        # Create blog posts
        created_count = 0
        for post_data in posts:
            # Check if post already exists
            if BlogPage.objects.filter(slug=post_data['slug']).exists():
                self.stdout.write(self.style.WARNING(f'Post "{post_data["title"]}" already exists, skipping'))
                continue

            try:
                blog_post = BlogPage(
                    title=post_data['title'],
                    slug=post_data['slug'],
                    intro=post_data['intro'],
                    body=post_data['body_blocks'],  # Use StreamField blocks
                    date='2025-10-14'
                )

                blog_index.add_child(instance=blog_post)

                # Set tags
                for tag_name in post_data['tags']:
                    blog_post.tags.add(tag_name)

                # Publish the post
                blog_post.save_revision().publish()
                created_count += 1

                self.stdout.write(self.style.SUCCESS(f'✓ Created blog post: "{post_data["title"]}"'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating post "{post_data["title"]}": {e}'))

        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} blog posts!'))
        self.stdout.write(self.style.SUCCESS('View them at: http://localhost:8000/admin/pages/ or http://localhost:3000/blog'))
