"""
Management command to create a sample step-based exercise for testing.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from wagtail.models import Page
from apps.blog.models import StepBasedExercisePage, LessonPage
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a sample step-based exercise for testing multi-step functionality'

    def handle(self, *args, **options):
        self.stdout.write('Creating step-based exercise...')
        
        # Get or create admin user
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            self.stdout.write(self.style.WARNING('No admin user found, creating one...'))
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123'
            )
        
        # Find a lesson to attach the exercise to
        lesson = LessonPage.objects.live().first()
        if not lesson:
            self.stdout.write(self.style.ERROR('No lesson found. Please create a lesson first.'))
            return
        
        # Check if exercise already exists
        if StepBasedExercisePage.objects.filter(slug='build-calculator').exists():
            self.stdout.write(self.style.WARNING('Step-based exercise already exists, skipping creation.'))
            return
        
        # Create step-based exercise
        exercise = StepBasedExercisePage(
            title='Build a Python Calculator',
            slug='build-calculator',
            require_sequential=True,
            total_points=100,
            difficulty='medium',
            estimated_time=45,
            exercise_steps=[
                {
                    'type': 'exercise_step',
                    'value': {
                        'step_number': 1,
                        'title': 'Create Basic Variables',
                        'description': '<p>Let\'s start by creating variables to store two numbers for our calculator.</p><p>Create two variables: <code>num1</code> with value 10 and <code>num2</code> with value 5.</p>',
                        'exercise_type': 'fill_blank',
                        'template': '# Create variables for our calculator\n{{BLANK_1}} = {{BLANK_2}}\n{{BLANK_3}} = {{BLANK_4}}\n\nprint(f"Number 1: {num1}")\nprint(f"Number 2: {num2}")',
                        'solutions': json.dumps({
                            "1": "num1",
                            "2": "10",
                            "3": "num2", 
                            "4": "5"
                        }),
                        'points': 20,
                        'success_message': 'Excellent! You\'ve created the basic variables.',
                        'hint': 'Remember to use descriptive variable names and assign the correct values.'
                    }
                },
                {
                    'type': 'exercise_step',
                    'value': {
                        'step_number': 2,
                        'title': 'Implement Addition',
                        'description': '<p>Now let\'s create a function to add two numbers together.</p><p>Complete the function definition and return statement.</p>',
                        'exercise_type': 'fill_blank',
                        'template': '# Define addition function\n{{BLANK_1}} add(a, b):\n    {{BLANK_2}} a + b\n\n# Test the function\nresult = add(10, 5)\nprint(f"10 + 5 = {result}")',
                        'solutions': json.dumps({
                            "1": "def",
                            "2": "return"
                        }),
                        'points': 20,
                        'success_message': 'Great! Your addition function works perfectly.',
                        'hint': 'Functions in Python are defined with a specific keyword, and they send values back with another keyword.'
                    }
                },
                {
                    'type': 'exercise_step',
                    'value': {
                        'step_number': 3,
                        'title': 'Add Subtraction',
                        'description': '<p>Let\'s add a subtraction function to our calculator.</p><p>Create a function that subtracts the second number from the first.</p>',
                        'exercise_type': 'fill_blank',
                        'template': '# Define subtraction function\ndef {{BLANK_1}}(a, b):\n    return {{BLANK_2}} - {{BLANK_3}}\n\n# Test the function\nresult = subtract(10, 5)\nprint(f"10 - 5 = {result}")',
                        'solutions': json.dumps({
                            "1": "subtract",
                            "2": "a",
                            "3": "b"
                        }),
                        'points': 20,
                        'success_message': 'Perfect! Subtraction is working correctly.',
                        'hint': 'The function name should describe what it does, and subtraction order matters.'
                    }
                },
                {
                    'type': 'exercise_step',
                    'value': {
                        'step_number': 4,
                        'title': 'Implement Multiplication',
                        'description': '<p>Add multiplication capability to your calculator.</p><p>Create a function that multiplies two numbers.</p>',
                        'exercise_type': 'fill_blank',
                        'template': '# Define multiplication function\ndef multiply({{BLANK_1}}, {{BLANK_2}}):\n    return a {{BLANK_3}} b\n\n# Test the function\nresult = multiply(10, 5)\nprint(f"10 × 5 = {result}")',
                        'solutions': json.dumps({
                            "1": "a",
                            "2": "b",
                            "3": "*"
                        }),
                        'points': 20,
                        'success_message': 'Wonderful! Multiplication is now available.',
                        'hint': 'Remember the multiplication operator in Python is an asterisk.'
                    }
                },
                {
                    'type': 'exercise_step',
                    'value': {
                        'step_number': 5,
                        'title': 'Complete with Division',
                        'description': '<p>Finally, let\'s add division to complete our basic calculator.</p><p>Create a division function with proper error handling for division by zero.</p>',
                        'exercise_type': 'fill_blank',
                        'template': '# Define division function with error handling\ndef divide(a, b):\n    if {{BLANK_1}} == 0:\n        return "Error: Cannot divide by zero"\n    return {{BLANK_2}} / {{BLANK_3}}\n\n# Test the function\nresult1 = divide(10, 5)\nresult2 = divide(10, 0)\nprint(f"10 ÷ 5 = {result1}")\nprint(f"10 ÷ 0 = {result2}")',
                        'solutions': json.dumps({
                            "1": "b",
                            "2": "a",
                            "3": "b"
                        }),
                        'points': 20,
                        'success_message': 'Congratulations! You\'ve built a complete calculator with all four operations!',
                        'hint': 'Check the divisor (second parameter) before performing division.'
                    }
                }
            ],
            general_hints=[
                {
                    'type': 'hint',
                    'value': {
                        'hint_text': '<p>Remember that Python is case-sensitive. Variable names and function names must match exactly.</p>',
                        'show_after_step': 0
                    }
                },
                {
                    'type': 'hint',
                    'value': {
                        'hint_text': '<p>Functions help us organize code into reusable blocks. Each function should do one specific task.</p>',
                        'show_after_step': 1
                    }
                },
                {
                    'type': 'hint',
                    'value': {
                        'hint_text': '<p>Always handle edge cases like division by zero to make your code more robust.</p>',
                        'show_after_step': 3
                    }
                }
            ],
            completion_message='<p><strong>🎉 Fantastic work!</strong></p><p>You\'ve successfully built a complete Python calculator with:</p><ul><li>Addition</li><li>Subtraction</li><li>Multiplication</li><li>Division (with error handling)</li></ul><p>You\'ve learned about variables, functions, parameters, return values, and error handling. These are fundamental concepts that you\'ll use in every Python program you write!</p>',
            show_completion_certificate=True
        )
        
        # Add as child of lesson
        try:
            lesson.add_child(instance=exercise)
        except AttributeError:
            # If add_child fails, save and set parent manually
            exercise.set_url_path(lesson)
            exercise.save()
            exercise.move(lesson, pos='last-child')
        
        # Publish the exercise
        revision = exercise.save_revision(user=admin_user)
        revision.publish()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created step-based exercise: {exercise.title}'))
        self.stdout.write(f'URL: /step-exercises/{exercise.slug}')
        self.stdout.write(f'Total steps: 5')
        self.stdout.write(f'Total points: {exercise.total_points}')