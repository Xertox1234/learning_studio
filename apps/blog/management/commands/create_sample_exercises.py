"""
Management command to create sample exercises for testing the Wagtail exercise system.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.blog.models import (
    HomePage, LearningIndexPage, CoursePage, LessonPage, 
    ExercisePage, StepBasedExercisePage, SkillLevel, BlogCategory
)
import json

User = get_user_model()


class Command(BaseCommand):
    help = 'Create sample exercises for testing the Wagtail exercise system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete',
            action='store_true',
            help='Delete existing sample exercises first',
        )

    def handle(self, *args, **options):
        if options['delete']:
            self.stdout.write('Deleting existing sample exercises...')
            ExercisePage.objects.filter(title__startswith='Sample').delete()
            StepBasedExercisePage.objects.filter(title__startswith='Sample').delete()

        self.stdout.write('Creating sample exercises...')

        # Get or create necessary parent pages
        home_page = HomePage.objects.first()
        if not home_page:
            self.stdout.write(self.style.ERROR('No HomePage found. Please run create_wagtail_site first.'))
            return

        # Find or create a course to add exercises to
        course_page = CoursePage.objects.filter(live=True).first()
        if not course_page:
            self.stdout.write('Creating a sample course for exercises...')
            learning_page = LearningIndexPage.objects.first()
            if not learning_page:
                learning_page = LearningIndexPage(
                    title="Learning Hub",
                    intro="Welcome to our learning platform"
                )
                home_page.add_child(instance=learning_page)
                learning_page.save_revision().publish()

            # Get skill level
            skill_level = SkillLevel.objects.first()
            if not skill_level:
                skill_level = SkillLevel.objects.create(
                    name="Beginner",
                    slug="beginner",
                    description="For beginners",
                    color="green",
                    order=1
                )

            course_page = CoursePage(
                title="Python Programming Fundamentals",
                slug="python-fundamentals",
                course_code="PY101",
                short_description="Learn Python programming from the ground up",
                difficulty_level="beginner",
                estimated_duration="4 weeks",
                is_free=True,
                featured=True,
                skill_level=skill_level
            )
            learning_page.add_child(instance=course_page)
            course_page.save_revision().publish()

        # Find or create a lesson within the course
        lesson_page = course_page.get_children().live().type(LessonPage).first()
        if not lesson_page:
            self.stdout.write('Creating a sample lesson for exercises...')
            lesson_page = LessonPage(
                title="Variables and Data Types",
                slug="variables-data-types",
                lesson_number=1,
                estimated_duration=45,
                difficulty_level="beginner"
            )
            course_page.add_child(instance=lesson_page)
            lesson_page.save_revision().publish()

        # Create sample regular exercises
        self.create_fill_blank_exercise(lesson_page)
        self.create_coding_exercise(lesson_page)
        self.create_multiple_choice_exercise(lesson_page)
        
        # Create sample step-based exercise
        self.create_step_based_exercise(lesson_page)

        self.stdout.write(self.style.SUCCESS('Successfully created sample exercises'))

    def create_fill_blank_exercise(self, parent_page):
        """Create a fill-in-the-blank exercise"""
        self.stdout.write('Creating fill-in-the-blank exercise...')
        
        progressive_hints = [
            {
                "level": 1,
                "type": "conceptual",
                "title": "Think About Variables",
                "content": "What do you need to store a person's name in Python?",
                "triggerTime": 30,
                "triggerAttempts": 0
            },
            {
                "level": 2,
                "type": "syntax",
                "title": "Variable Assignment",
                "content": "In Python, you assign values to variables using the = operator.",
                "triggerTime": 90,
                "triggerAttempts": 2
            },
            {
                "level": 3,
                "type": "solution",
                "title": "Complete Answer",
                "content": "Use 'name' as the variable and assign it a string value like 'John'.",
                "triggerTime": 180,
                "triggerAttempts": 3
            }
        ]

        solutions = {
            "1": "name",
            "2": "John",
            "3": "print",
            "4": "name"
        }

        alternative_solutions = {
            "1": ["name", "user_name", "person_name"],
            "2": ["John", "Alice", "Bob", "Mary", "'John'", '"John"'],
            "3": ["print", "Print"],
            "4": ["name", "user_name", "person_name"]
        }

        exercise = ExercisePage(
            title="Sample: Python Variables",
            slug="sample-python-variables",
            exercise_type="fill_blank",
            difficulty="easy",
            points=15,
            layout_type="standard",
            programming_language="python",
            description="<p>Learn how to create and use variables in Python by completing this fill-in-the-blank exercise.</p>",
            template_code='''# Create a variable to store a person's name
{{BLANK_1}} = "{{BLANK_2}}"

# Print the variable
{{BLANK_3}}({{BLANK_4}})''',
            solutions=solutions,
            alternative_solutions=alternative_solutions,
            progressive_hints=progressive_hints,
            time_limit=10,
            show_sidebar=True,
            code_editor_height="200px"
        )
        
        parent_page.add_child(instance=exercise)
        exercise.save_revision().publish()
        self.stdout.write('  ✓ Fill-in-the-blank exercise created')

    def create_coding_exercise(self, parent_page):
        """Create a coding exercise"""
        self.stdout.write('Creating coding exercise...')

        exercise = ExercisePage(
            title="Sample: Calculate Circle Area",
            slug="sample-circle-area",
            exercise_type="coding",
            difficulty="medium",
            points=25,
            layout_type="standard",
            programming_language="python",
            description="<p>Write a Python function that calculates the area of a circle given its radius.</p><p>The formula for the area of a circle is: <strong>π × r²</strong></p>",
            starter_code='''import math

def calculate_circle_area(radius):
    """
    Calculate the area of a circle given its radius.
    
    Args:
        radius (float): The radius of the circle
    
    Returns:
        float: The area of the circle
    """
    # Your code here
    pass

# Test your function
radius = 5
area = calculate_circle_area(radius)
print(f"The area of a circle with radius {radius} is {area}")''',
            solution_code='''import math

def calculate_circle_area(radius):
    """
    Calculate the area of a circle given its radius.
    
    Args:
        radius (float): The radius of the circle
    
    Returns:
        float: The area of the circle
    """
    return math.pi * radius ** 2

# Test your function
radius = 5
area = calculate_circle_area(radius)
print(f"The area of a circle with radius {radius} is {area}")''',
            time_limit=15,
            max_attempts=5,
            show_sidebar=True,
            code_editor_height="400px"
        )
        
        parent_page.add_child(instance=exercise)
        exercise.save_revision().publish()
        self.stdout.write('  ✓ Coding exercise created')

    def create_multiple_choice_exercise(self, parent_page):
        """Create a multiple choice exercise"""
        self.stdout.write('Creating multiple choice exercise...')

        question_data = {
            "question": "Which of the following is the correct way to create a list in Python?",
            "options": [
                "my_list = [1, 2, 3]",
                "my_list = (1, 2, 3)",
                "my_list = {1, 2, 3}",
                "my_list = <1, 2, 3>"
            ],
            "correct_answer": 0,
            "explanation": "Square brackets [ ] are used to create lists in Python. Parentheses create tuples, curly braces create sets or dictionaries, and angle brackets are not valid Python syntax."
        }

        exercise = ExercisePage(
            title="Sample: Python Lists",
            slug="sample-python-lists",
            exercise_type="multiple_choice",
            difficulty="easy",
            points=10,
            layout_type="standard",
            programming_language="python",
            description="<p>Test your knowledge of Python list syntax with this multiple choice question.</p>",
            question_data=question_data,
            time_limit=5,
            show_sidebar=True
        )
        
        parent_page.add_child(instance=exercise)
        exercise.save_revision().publish()
        self.stdout.write('  ✓ Multiple choice exercise created')

    def create_step_based_exercise(self, parent_page):
        """Create a step-based exercise"""
        self.stdout.write('Creating step-based exercise...')

        exercise = StepBasedExercisePage(
            title="Sample: Build a Calculator",
            slug="sample-calculator",
            difficulty="medium",
            total_points=50,
            estimated_time=20,
            require_sequential=True
        )
        
        # Add steps to the exercise
        exercise.exercise_steps = [
            ('exercise_step', {
                'step_number': 1,
                'title': 'Create Variables',
                'description': '<p>Create two variables to store numbers that we will use in our calculator.</p>',
                'exercise_type': 'fill_blank',
                'template': '''# Step 1: Create two variables for our calculator
{{BLANK_1}} = {{BLANK_2}}
{{BLANK_3}} = {{BLANK_4}}''',
                'solutions': '{"1": "num1", "2": "10", "3": "num2", "4": "5"}',
                'points': 10,
                'success_message': 'Great! You\'ve created the variables we need.',
                'hint': 'Variables in Python are created by assigning values with the = operator.'
            }),
            ('exercise_step', {
                'step_number': 2,
                'title': 'Addition Function',
                'description': '<p>Now create a function that adds two numbers together.</p>',
                'exercise_type': 'fill_blank',
                'template': '''def {{BLANK_1}}(a, b):
    return a {{BLANK_2}} b''',
                'solutions': '{"1": "add", "2": "+"}',
                'points': 15,
                'success_message': 'Perfect! Your addition function is working.',
                'hint': 'The function name should describe what it does, and use + for addition.'
            }),
            ('exercise_step', {
                'step_number': 3,
                'title': 'Test the Calculator',
                'description': '<p>Finally, use your function to calculate the sum and print the result.</p>',
                'exercise_type': 'fill_blank',
                'template': '''# Test the calculator
result = {{BLANK_1}}({{BLANK_2}}, {{BLANK_3}})
{{BLANK_4}}(f"The sum is: {result}")''',
                'solutions': '{"1": "add", "2": "num1", "3": "num2", "4": "print"}',
                'points': 25,
                'success_message': 'Congratulations! You\'ve built a working calculator.',
                'hint': 'Use the function name you created and the variables from step 1.'
            })
        ]
        
        parent_page.add_child(instance=exercise)
        exercise.save_revision().publish()
        self.stdout.write('  ✓ Step-based exercise created')