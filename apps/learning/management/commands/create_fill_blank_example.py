"""
Django management command to create a fill-in-the-blank example lesson matching the screenshot.
"""

from django.core.management.base import BaseCommand
from apps.learning.models import Lesson, Course


class Command(BaseCommand):
    help = 'Create a fill-in-the-blank example lesson matching the screenshot'

    def handle(self, *args, **options):
        # Get the structured content examples course
        try:
            course = Course.objects.get(slug='structured-content-examples')
        except Course.DoesNotExist:
            self.stderr.write("Structured Content Examples course not found.")
            return

        self.stdout.write(f"Creating fill-in-the-blank example for course: {course.title}")

        # Create the lesson exactly like the screenshot
        lesson, created = Lesson.objects.get_or_create(
            title='Basic Python Variables (Fill in the Blanks)',
            course=course,
            defaults={
                'slug': 'python-variables-fill-blanks',
                'description': 'Practice creating variables with fill-in-the-blank exercises',
                'lesson_type': 'practical',
                'difficulty_level': 'beginner',
                'order': 4,
                'estimated_duration': 15,
                'enable_structured_content': True,
                'content_format': 'structured',
                'is_published': True
            }
        )

        if not created:
            self.stdout.write(f"Lesson '{lesson.title}' already exists, updating content...")

        # Create content exactly matching the screenshot
        lesson.structured_content = [
            {
                'type': 'heading',
                'content': 'Basic Python Variables',
                'level': 2,
                'id': 0
            },
            {
                'type': 'alert',
                'alert_type': 'info',
                'title': 'Instructions',
                'content': '''<strong>Goal:</strong> Create variables to store personal information and display them.<br><br>
                • <strong>Name:</strong> Enter any name as a string (must include quotes: "John" or "Mary")<br>
                • <strong>Age:</strong> Enter any whole number between 18-65 (like 25 or 30)<br>
                • <strong>Student status:</strong> Enter exactly True or False (capital T/F)<br><br>
                ✅ <strong>Valid examples:</strong> name = "Sarah", age = 28, is_student = True<br>
                ✅ <strong>Also valid:</strong> name = "Mike", age = 45, is_student = False''',
                'id': 1
            },
            {
                'type': 'interactive_code',
                'content': '''# Python variables and basic operations
name = {{BLANK_1}}
age = {{BLANK_2}}
is_student = {{BLANK_3}}

print(f"Hello, my name is {name}")
print(f"I am {age} years old")
print(f"Am I a student? {is_student}")''',
                'language': 'python',
                'exercise_type': 'fill_blank',
                'blanks': [
                    {'id': 'BLANK_1', 'placeholder': 'YourName', 'type': 'text'},
                    {'id': 'BLANK_2', 'placeholder': '18-65', 'type': 'text'}, 
                    {'id': 'BLANK_3', 'placeholder': 'True/False', 'type': 'text'}
                ],
                'expected_output': '''Hello, my name is YourName
I am YourAge years old
Am I a student? True/False''',
                'id': 2
            }
        ]

        lesson.save()
        self.stdout.write(
            self.style.SUCCESS(f'✓ Created/updated lesson: {lesson.title}')
        )
        self.stdout.write(
            f'  URL: /courses/{course.slug}/lessons/{lesson.slug}/'
        )