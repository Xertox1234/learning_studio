"""
Django management command to migrate LessonPage objects to ExercisePage objects.
This creates simple code-to-run exercises (like the demo) from lesson content.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.blog.models import CoursePage, LessonPage, ExercisePage
import json


class Command(BaseCommand):
    help = 'Migrate LessonPage objects to ExercisePage objects (demo-style coding exercises)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would happen without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        courses = CoursePage.objects.all()

        for course in courses:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Migrating: {course.title}")
            self.stdout.write('='*60)

            self.migrate_course(course, dry_run)

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✅ Migration complete!'))

    def migrate_course(self, course, dry_run=False):
        """Migrate a single course from lessons to exercises."""
        lessons = course.get_children().type(LessonPage).specific().order_by('path')

        self.stdout.write(f"\n  Found {lessons.count()} lessons to convert\n")

        sequence_number = 1

        for lesson in lessons:
            self.stdout.write(f"  📖 Converting Lesson {lesson.lesson_number}: {lesson.title}")

            # Extract code examples from lesson content
            code_example = self.extract_code_example(lesson)

            if not dry_run:
                exercise = ExercisePage(
                    title=lesson.title,
                    slug=lesson.slug,
                    sequence_number=sequence_number,
                    exercise_type='coding',  # Simple coding exercise like demo
                    difficulty=self.determine_difficulty(lesson.lesson_number),
                    points=self.calculate_points(lesson.lesson_number),
                    layout_type='standard',
                    show_sidebar=True,
                    code_editor_height=400,
                    description=self.create_description(lesson),
                    starter_code=code_example,  # Set starter code for demo exercises
                    solution_code='',  # We don't provide solutions
                    template_code=code_example,  # The code to study/run
                    solutions={},
                    alternative_solutions={},
                    progressive_hints=self.create_hints(lesson),
                    programming_language='python',
                    test_cases=None,
                    hints=None,
                    question_data=None,
                    exercise_content=None,
                    time_limit=None,
                    max_attempts=None
                )

                # Add as child of course
                course.add_child(instance=exercise)
                exercise.save_revision().publish()

                # Unpublish and rename old lesson (keep for reference)
                lesson.unpublish()
                lesson.slug = f"{lesson.slug}-old"
                lesson.save()

                self.stdout.write(f"    ✅ Created exercise #{sequence_number}: {exercise.title}")
                self.stdout.write(f"    ⚠️  Unpublished old lesson and renamed to {lesson.slug} (kept for reference)")
            else:
                self.stdout.write(f"    Would create exercise #{sequence_number}")

            sequence_number += 1

    def extract_code_example(self, lesson):
        """Extract a representative code example from lesson content."""
        # Parse lesson content StreamField to find code blocks
        if not lesson.content:
            return self.create_default_code(lesson)

        code_blocks = []
        for block in lesson.content:
            if block.block_type == 'code':
                code_blocks.append(block.value)
            elif block.block_type == 'python_example':
                if hasattr(block.value, 'get'):
                    code_blocks.append(block.value.get('code', ''))

        if code_blocks:
            # Use the first substantial code block
            for code in code_blocks:
                if len(code) > 20:  # Skip trivial examples
                    return code

        # Fallback: create example based on lesson title
        return self.create_default_code(lesson)

    def create_default_code(self, lesson):
        """Create a default code example based on lesson topic."""
        title_lower = lesson.title.lower()

        if 'variable' in title_lower and 'string' in title_lower:
            return '''# Variables and Strings
first_name = "Python"
last_name = "Programmer"
full_name = first_name + " " + last_name

print(f"Hello, {full_name}!")
print(f"Name length: {len(full_name)}")'''

        elif 'conditional' in title_lower or 'if' in title_lower:
            return '''# Conditional Logic
age = 18
has_license = True

if age >= 18 and has_license:
    print("You can drive!")
else:
    print("You cannot drive yet.")'''

        elif 'function' in title_lower:
            return '''# Functions
def greet(name):
    return f"Hello, {name}!"

def add(a, b):
    return a + b

print(greet("Python"))
print(f"5 + 3 = {add(5, 3)}")'''

        elif 'loop' in title_lower or 'for' in title_lower or 'while' in title_lower:
            return '''# Loops
for i in range(5):
    print(f"Count: {i}")

numbers = [1, 2, 3, 4, 5]
for num in numbers:
    print(f"Number: {num}")'''

        else:
            # Generic Python example
            return f'''# {lesson.title}
# Study and run this code example

print("Learning Python!")
print("Topic: {lesson.title}")'''

    def create_description(self, lesson):
        """Create description for the exercise."""
        return lesson.intro or f"Study and understand the code example about {lesson.title.lower()}. Run it to see how it works!"

    def create_hints(self, lesson):
        """Create progressive hints for the exercise."""
        hints = [
            {
                'level': 1,
                'type': 'conceptual',
                'title': 'Understanding the Goal',
                'content': f'<p>Study this code example about <strong>{lesson.title.lower()}</strong>.</p><p>Try to understand what each line does before running it.</p>',
                'triggerTime': 30,
                'triggerAttempts': 0
            },
            {
                'level': 2,
                'type': 'approach',
                'title': 'Run and Observe',
                'content': "<p>Click the 'Run' button to execute the code.</p><p>Observe the output carefully - what does it tell you about how this code works?</p>",
                'triggerTime': 60,
                'triggerAttempts': 0
            },
            {
                'level': 3,
                'type': 'structure',
                'title': 'Code Breakdown',
                'content': "<p>Let's break down the code line by line:</p><ul><li>What does the first line do?</li><li>What happens in the middle?</li><li>What's the final result?</li></ul>",
                'triggerTime': 120,
                'triggerAttempts': 0
            },
            {
                'level': 4,
                'type': 'near_solution',
                'title': 'Key Concepts',
                'content': f'<p>The main concepts in <strong>{lesson.title}</strong> are:</p><ul><li>Understanding the syntax</li><li>Knowing when to use this pattern</li><li>Recognizing the output</li></ul>',
                'triggerTime': 180,
                'triggerAttempts': 0
            },
            {
                'level': 5,
                'type': 'solution',
                'title': 'Summary',
                'content': f'<p>This example demonstrates the core concepts of <strong>{lesson.title.lower()}</strong>.</p><p>Try modifying the code to experiment and deepen your understanding!</p>',
                'triggerTime': 240,
                'triggerAttempts': 0
            }
        ]
        return json.dumps(hints)

    def determine_difficulty(self, lesson_number):
        """Determine difficulty based on lesson number."""
        if lesson_number <= 2:
            return 'easy'
        elif lesson_number <= 4:
            return 'medium'
        else:
            return 'hard'

    def calculate_points(self, lesson_number):
        """Calculate points based on lesson number."""
        base_points = 10
        return base_points + (lesson_number - 1) * 5
