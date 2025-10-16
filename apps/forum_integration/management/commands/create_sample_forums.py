"""
Management command to create sample forums with topics and posts for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from machina.apps.forum.models import Forum
from machina.apps.forum_conversation.models import Topic, Post
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample forums with topics and posts for testing the forum system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing sample forums before creating new ones',
        )

    def handle(self, *args, **options):
        self.stdout.write('Creating sample forums...')

        # Get or create a test user for posting
        test_user, created = User.objects.get_or_create(
            email='forum_demo@pythonlearning.studio',
            defaults={
                'username': 'forum_demo',
                'first_name': 'Forum',
                'last_name': 'Demo',
            }
        )
        if created:
            test_user.set_password('demo123')
            test_user.save()
            self.stdout.write(f'Created demo user: {test_user.email}')

        # Get or create additional demo users for variety
        demo_users = []
        demo_user_data = [
            ('alice@pythonlearning.studio', 'alice', 'Alice', 'Developer'),
            ('bob@pythonlearning.studio', 'bob', 'Bob', 'Student'),
            ('charlie@pythonlearning.studio', 'charlie', 'Charlie', 'Teacher'),
        ]

        for email, username, first_name, last_name in demo_user_data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
                self.stdout.write(f'Created demo user: {user.email}')
            demo_users.append(user)

        all_users = [test_user] + demo_users

        # Delete existing sample forums if requested
        if options['delete_existing']:
            sample_forums = Forum.objects.filter(
                slug__in=['general-discussion', 'python-help', 'project-showcase', 'learning-resources', 'feedback']
            )
            count = sample_forums.count()
            sample_forums.delete()
            self.stdout.write(f'Deleted {count} existing sample forums')

        # Get or create root forum (category)
        root_forum, created = Forum.objects.get_or_create(
            slug='root',
            defaults={
                'name': 'Root Forum',
                'description': 'Root forum for organization',
                'type': Forum.FORUM_CAT,
            }
        )
        if created:
            self.stdout.write('Created root forum')

        # Define sample forums with their topics
        forums_data = [
            {
                'name': 'General Discussion',
                'slug': 'general-discussion',
                'description': 'General discussions about Python programming and this learning platform',
                'topics': [
                    {
                        'subject': 'Welcome to the Python Learning Studio!',
                        'content': 'Hello everyone! Welcome to our Python learning community. Feel free to introduce yourself and share what brings you here.',
                        'user_index': 0,
                    },
                    {
                        'subject': 'What are you working on this week?',
                        'content': "Let's share what we're working on! I'm currently building a web scraper to collect data for a personal project.",
                        'user_index': 1,
                    },
                    {
                        'subject': 'Best resources for learning Python?',
                        'content': "I'm relatively new to Python and looking for good resources. What do you all recommend for beginners?",
                        'user_index': 2,
                    },
                    {
                        'subject': 'Python 3.12 new features discussion',
                        'content': "Has anyone tried the new Python 3.12 features? The improved error messages look really helpful!",
                        'user_index': 3,
                    },
                ],
            },
            {
                'name': 'Python Help',
                'slug': 'python-help',
                'description': 'Get help with Python programming questions and debugging',
                'topics': [
                    {
                        'subject': 'How to handle None values in dictionaries?',
                        'content': "I'm working with dictionaries and keep running into KeyError. What's the best way to handle missing keys?",
                        'user_index': 1,
                    },
                    {
                        'subject': 'List comprehension vs for loops - when to use which?',
                        'content': "I understand list comprehensions but I'm not sure when to use them vs traditional for loops. Any guidance?",
                        'user_index': 2,
                    },
                    {
                        'subject': 'Understanding decorators',
                        'content': "Can someone explain decorators in simple terms? I've read the docs but still confused about practical use cases.",
                        'user_index': 3,
                    },
                    {
                        'subject': 'Virtual environments not activating on Windows',
                        'content': "I created a virtual environment but can't seem to activate it on Windows. Getting permission errors.",
                        'user_index': 0,
                    },
                    {
                        'subject': 'Best practices for error handling',
                        'content': "What are the best practices for error handling in Python? Should I catch specific exceptions or use broad try-except blocks?",
                        'user_index': 1,
                    },
                ],
            },
            {
                'name': 'Project Showcase',
                'slug': 'project-showcase',
                'description': 'Share your Python projects and get feedback from the community',
                'topics': [
                    {
                        'subject': 'Built a personal finance tracker',
                        'content': "Just finished my personal finance tracker app! It uses pandas for data analysis and matplotlib for visualization. Happy to share the code!",
                        'user_index': 1,
                    },
                    {
                        'subject': 'My first web scraper',
                        'content': "Created my first web scraper using BeautifulSoup. It collects weather data from multiple sources. Still learning but it works!",
                        'user_index': 2,
                    },
                    {
                        'subject': 'Django blog with markdown support',
                        'content': "Built a blog using Django with markdown support for posts. Also added syntax highlighting for code snippets!",
                        'user_index': 3,
                    },
                ],
            },
            {
                'name': 'Learning Resources',
                'slug': 'learning-resources',
                'description': 'Share and discover Python learning resources, tutorials, and courses',
                'topics': [
                    {
                        'subject': 'Free Python courses on YouTube',
                        'content': "Here's a list of excellent free Python courses on YouTube that helped me get started: [list to be added]",
                        'user_index': 0,
                    },
                    {
                        'subject': 'Recommended books for intermediate Python',
                        'content': "Looking for book recommendations for intermediate Python developers. Already read 'Automate the Boring Stuff'.",
                        'user_index': 1,
                    },
                    {
                        'subject': 'Interactive coding challenges',
                        'content': "What are your favorite platforms for Python coding challenges? I've been using LeetCode and Codewars.",
                        'user_index': 2,
                    },
                ],
            },
            {
                'name': 'Feedback & Suggestions',
                'slug': 'feedback',
                'description': 'Share feedback about the platform and suggest new features',
                'topics': [
                    {
                        'subject': 'Love the new code editor!',
                        'content': "The new code editor with syntax highlighting is amazing! Makes learning so much easier.",
                        'user_index': 1,
                    },
                    {
                        'subject': 'Suggestion: Add mobile app',
                        'content': "Would it be possible to create a mobile app version? Would love to practice on the go.",
                        'user_index': 2,
                    },
                ],
            },
        ]

        with transaction.atomic():
            for forum_data in forums_data:
                # Create forum
                forum, created = Forum.objects.get_or_create(
                    slug=forum_data['slug'],
                    defaults={
                        'name': forum_data['name'],
                        'description': forum_data['description'],
                        'type': Forum.FORUM_POST,
                        'parent': root_forum,
                    }
                )

                if created:
                    self.stdout.write(f'Created forum: {forum.name}')
                else:
                    self.stdout.write(f'Forum already exists: {forum.name}')

                # Create topics for this forum
                for topic_data in forum_data['topics']:
                    user = all_users[topic_data['user_index']]

                    # Check if topic already exists
                    existing_topic = Topic.objects.filter(
                        forum=forum,
                        subject=topic_data['subject']
                    ).first()

                    if existing_topic:
                        self.stdout.write(f'  Topic already exists: {topic_data["subject"]}')
                        continue

                    # Create topic
                    from django.utils.text import slugify
                    subject = topic_data['subject']

                    # Debug: verify subject is not empty
                    if not subject or not subject.strip():
                        self.stdout.write(f'  ⚠ WARNING: Empty subject for topic in {forum.name}!')
                        continue

                    topic = Topic.objects.create(
                        forum=forum,
                        subject=subject.strip(),
                        slug=slugify(subject),
                        poster=user,
                        type=Topic.TOPIC_POST,
                        status=Topic.TOPIC_UNLOCKED,
                        approved=True,
                        created=timezone.now(),
                        updated=timezone.now()
                    )

                    # Create the first post
                    post = Post.objects.create(
                        topic=topic,
                        poster=user,
                        subject=subject.strip(),  # Add subject to post
                        content=topic_data['content'],
                        approved=True,
                        created=timezone.now(),
                        updated=timezone.now()
                    )

                    # Update topic's first/last post
                    topic.first_post = post
                    topic.last_post = post
                    topic.posts_count = 1
                    # Only update specific fields to avoid overwriting subject
                    topic.save(update_fields=['first_post', 'last_post', 'posts_count', 'updated'])

                    self.stdout.write(f'  ✓ Created topic: {topic.subject}')

        # Print summary
        total_forums = len(forums_data)
        total_topics = sum(len(f['topics']) for f in forums_data)

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Sample data creation complete!'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {total_forums} forums with {total_topics} topics'
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {len(all_users)} demo users'
            )
        )
        self.stdout.write('\nDemo user credentials:')
        self.stdout.write('  forum_demo@pythonlearning.studio / demo123')
        self.stdout.write('  alice@pythonlearning.studio / demo123')
        self.stdout.write('  bob@pythonlearning.studio / demo123')
        self.stdout.write('  charlie@pythonlearning.studio / demo123')
